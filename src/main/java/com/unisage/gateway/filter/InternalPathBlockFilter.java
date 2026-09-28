package com.unisage.gateway.filter;

import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

/** Rejects /api/v1/{master,ai}/internal/** before AuthenticationFilter runs, on the raw path. */
@Component
public class InternalPathBlockFilter implements GlobalFilter, Ordered {

    private static final Logger log = LoggerFactory.getLogger(InternalPathBlockFilter.class);

    private static final int MAX_DECODE_PASSES = 3;

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String rawPath = exchange.getRequest().getURI().getRawPath();
        if (rawPath == null) {
            return chain.filter(exchange);
        }

        String lowerRaw = rawPath.toLowerCase(Locale.ROOT);
        if (!startsWithGuardedPrefix(lowerRaw, "/api/v1/master") && !startsWithGuardedPrefix(lowerRaw, "/api/v1/ai")) {
            return chain.filter(exchange);
        }

        if (containsSuspiciousEncoding(rawPath)) {
            return reject(exchange, rawPath);
        }

        String normalized = normalize(rawPath);
        if (normalized.startsWith("/api/v1/master/internal/") || normalized.equals("/api/v1/master/internal")
                || normalized.startsWith("/api/v1/ai/internal/") || normalized.equals("/api/v1/ai/internal")) {
            return reject(exchange, rawPath);
        }

        return chain.filter(exchange);
    }

    /** True if lowerRaw is exactly prefix, or prefix followed by '/' or ';' (matrix params). */
    private boolean startsWithGuardedPrefix(String lowerRaw, String prefix) {
        if (!lowerRaw.startsWith(prefix)) {
            return false;
        }
        if (lowerRaw.length() == prefix.length()) {
            return true;
        }
        char next = lowerRaw.charAt(prefix.length());
        return next == '/' || next == ';';
    }

    private boolean containsSuspiciousEncoding(String rawPath) {
        String lower = rawPath.toLowerCase(Locale.ROOT);
        return lower.contains("%2f") || lower.contains("%5c") || lower.contains("%2e") || lower.contains("%25")
                || rawPath.contains("\\") || rawPath.contains(";");
    }

    private String normalize(String rawPath) {
        String decoded = rawPath;
        for (int i = 0; i < MAX_DECODE_PASSES; i++) {
            String next = URLDecoder.decode(decoded, StandardCharsets.UTF_8);
            if (next.equals(decoded)) {
                break;
            }
            decoded = next;
        }
        decoded = decoded.replaceAll("/{2,}", "/");
        decoded = resolveDotSegments(decoded);
        return decoded.toLowerCase(Locale.ROOT);
    }

    private String resolveDotSegments(String path) {
        String[] segments = path.split("/", -1);
        java.util.Deque<String> stack = new java.util.ArrayDeque<>();
        for (String segment : segments) {
            if (segment.isEmpty() || ".".equals(segment)) {
                continue;
            }
            if ("..".equals(segment)) {
                if (!stack.isEmpty()) {
                    stack.removeLast();
                }
                continue;
            }
            stack.addLast(segment);
        }
        StringBuilder sb = new StringBuilder("/");
        sb.append(String.join("/", stack));
        return sb.toString();
    }

    private Mono<Void> reject(ServerWebExchange exchange, String rawPath) {
        log.warn("Blocked external access to internal path: {}", rawPath);
        ServerHttpResponse response = exchange.getResponse();
        response.setStatusCode(HttpStatus.NOT_FOUND);
        return response.setComplete();
    }

    @Override
    public int getOrder() {
        return Ordered.HIGHEST_PRECEDENCE;
    }
}

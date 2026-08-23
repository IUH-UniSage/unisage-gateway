package com.unisage.gateway.filter;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.unisage.gateway.security.JwtValidator;
import io.jsonwebtoken.Claims;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpCookie;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.PathContainer;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.util.pattern.PathPattern;
import org.springframework.web.util.pattern.PathPatternParser;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Optional;

@Component
public class AuthenticationFilter implements GlobalFilter, Ordered {

    private static final Logger log = LoggerFactory.getLogger(AuthenticationFilter.class);

    private final JwtValidator jwtValidator;
    private final ObjectMapper objectMapper;
    private final List<PathPattern> publicPathPatterns;

    private static final String ACCESS_TOKEN_COOKIE_NAME = "accessToken";
    private static final String DEPARTMENT_ACCESS_HEADER = "X-User-Department-Access";
    private static final String PERMISSIONS_HEADER = "X-User-Permissions";
    private static final String EMPTY_JSON_ARRAY = "[]";

    private static final List<String> PUBLIC_PATHS = List.of(
            "/api/v1/master/auth/**",
            "/api/v1/ai/chat/stream",
            "/swagger-ui/**",
            "/v3/api-docs/**",
            "/swagger-resources/**",
            "/webjars/**",
            "/actuator/health"
    );

    public AuthenticationFilter(JwtValidator jwtValidator, ObjectMapper objectMapper) {
        this.jwtValidator = jwtValidator;
        this.objectMapper = objectMapper;
        PathPatternParser parser = new PathPatternParser();
        this.publicPathPatterns = PUBLIC_PATHS.stream()
                .map(parser::parse)
                .toList();
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();

        if (isPreflightRequest(request)) {
            return chain.filter(exchange);
        }

        String requestId = request.getHeaders().getFirst("X-Request-ID");
        if (requestId == null) {
            requestId = java.util.UUID.randomUUID().toString();
        }

        ServerHttpRequest.Builder requestBuilder = request.mutate()
                .header("X-Request-ID", requestId);

        String path = request.getURI().getPath();
        log.debug("Gateway matching path: {} [Trace ID: {}]", path, requestId);

        if (isPublicPath(path)) {
            return chain.filter(exchange.mutate().request(requestBuilder.build()).build());
        }

        String token = extractToken(request);
        Optional<Claims> claims = token == null ? Optional.empty() : jwtValidator.parseIfValidAccessToken(token);

        if (claims.isEmpty()) {
            log.warn("Invalid token for path: {} [Trace ID: {}]", path, requestId);
            return onError(exchange, HttpStatus.UNAUTHORIZED, "Unauthenticated");
        }

        requestBuilder.header(HttpHeaders.AUTHORIZATION, "Bearer " + token);
        requestBuilder.header(DEPARTMENT_ACCESS_HEADER, toJsonArray(claims.get().get("department_access", List.class)));
        requestBuilder.header(PERMISSIONS_HEADER, toJsonArray(claims.get().get("permissions", List.class)));

        return chain.filter(exchange.mutate().request(requestBuilder.build()).build());
    }

    private String toJsonArray(List<?> claimValue) {
        if (claimValue == null) {
            return EMPTY_JSON_ARRAY;
        }
        try {
            return objectMapper.writeValueAsString(claimValue);
        } catch (JsonProcessingException e) {
            log.warn("Failed to serialize JWT claim to JSON — falling back to empty array", e);
            return EMPTY_JSON_ARRAY;
        }
    }

    private boolean isPublicPath(String path) {
        PathContainer pathContainer = PathContainer.parsePath(path);
        return publicPathPatterns.stream().anyMatch(pattern -> pattern.matches(pathContainer));
    }

    private boolean isPreflightRequest(ServerHttpRequest request) {
        return org.springframework.http.HttpMethod.OPTIONS.equals(request.getMethod())
                && request.getHeaders().containsKey(HttpHeaders.ORIGIN)
                && request.getHeaders().containsKey(HttpHeaders.ACCESS_CONTROL_REQUEST_METHOD);
    }

    private String extractToken(ServerHttpRequest request) {
        String authHeader = request.getHeaders().getFirst(HttpHeaders.AUTHORIZATION);
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            return authHeader.substring(7);
        }
        HttpCookie cookie = request.getCookies().getFirst(ACCESS_TOKEN_COOKIE_NAME);
        if (cookie != null) {
            return cookie.getValue();
        }
        return null;
    }

    private Mono<Void> onError(ServerWebExchange exchange, HttpStatus status, String err) {
        ServerHttpResponse response = exchange.getResponse();
        response.setStatusCode(status);
        response.getHeaders().add(HttpHeaders.CONTENT_TYPE, "application/json");

        String body = String.format("{\"code\": %d, \"message\": \"%s\"}", 1001, err);
        byte[] bytes = body.getBytes();

        return response.writeWith(Mono.just(response.bufferFactory().wrap(bytes)));
    }

    @Override
    public int getOrder() {
        return -1;
    }
}

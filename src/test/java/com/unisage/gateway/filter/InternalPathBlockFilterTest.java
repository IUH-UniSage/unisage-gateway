package com.unisage.gateway.filter;

import java.net.URI;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.http.HttpStatus;
import org.springframework.mock.http.server.reactive.MockServerHttpRequest;
import org.springframework.mock.web.server.MockServerWebExchange;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import static org.assertj.core.api.Assertions.assertThat;

class InternalPathBlockFilterTest {

    private final InternalPathBlockFilter filter = new InternalPathBlockFilter();

    /** Records whether the chain was invoked, without a real backend behind it. */
    private static class CapturingChain implements GatewayFilterChain {
        AtomicReference<ServerWebExchange> captured = new AtomicReference<>();

        @Override
        public Mono<Void> filter(ServerWebExchange exchange) {
            captured.set(exchange);
            return Mono.empty();
        }
    }

    private MockServerWebExchange exchangeFor(String rawPath) {
        MockServerHttpRequest request = MockServerHttpRequest.method(org.springframework.http.HttpMethod.GET,
                URI.create(rawPath)).build();
        return MockServerWebExchange.from(request);
    }

    @ParameterizedTest
    @ValueSource(strings = {
            "/api/v1/master/internal/model-registry/snapshot",
            "/api/v1/master/internal/model-registry/verifications/claim",
            "/api/v1/master/internal/model-registry/embedding-index/unisage_chunks/identity",
            "/api/v1/ai/internal/whatever",
            "/api/v1/master/INTERNAL/model-registry/snapshot",
            "/api/v1/master/%69nternal/model-registry/snapshot",
            "/api/v1/master//internal/model-registry/snapshot",
            "/api/v1/master/x/../internal/model-registry/snapshot",
    })
    void guardedPaths_blockedWith404_chainNeverCalled(String rawPath) {
        MockServerWebExchange exchange = exchangeFor(rawPath);
        CapturingChain chain = new CapturingChain();

        filter.filter(exchange, chain).block();

        assertThat(exchange.getResponse().getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        assertThat(chain.captured.get()).isNull();
    }

    @ParameterizedTest
    @ValueSource(strings = {
            "/api/v1/master/x/%2E%2E/internal/model-registry/snapshot",
            "/api/v1/master/x%2F..%2Finternal/model-registry/snapshot",
            "/api/v1/master/%252E%252E/internal/model-registry/snapshot",
            "/api/v1/master/internal;a=b/model-registry/snapshot",
            "/api/v1/master;x=y/internal/model-registry/snapshot",
    })
    void suspiciousEncoding_rejectedWithoutDecoding(String rawPath) {
        MockServerWebExchange exchange = exchangeFor(rawPath);
        CapturingChain chain = new CapturingChain();

        filter.filter(exchange, chain).block();

        assertThat(exchange.getResponse().getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        assertThat(chain.captured.get()).isNull();
    }

    @ParameterizedTest
    @ValueSource(strings = {
            "/api/v1/master/chat-models",
            "/api/v1/master/internal-docs",
            "/api/v1/ai/chat/stream",
    })
    void nonInternalPaths_passThrough(String rawPath) {
        MockServerWebExchange exchange = exchangeFor(rawPath);
        CapturingChain chain = new CapturingChain();

        filter.filter(exchange, chain).block();

        assertThat(chain.captured.get()).isNotNull();
    }

    @Test
    void order_runsBeforeAuthenticationFilter() {
        assertThat(filter.getOrder()).isLessThan(new AuthenticationFilter(null, null).getOrder());
    }
}

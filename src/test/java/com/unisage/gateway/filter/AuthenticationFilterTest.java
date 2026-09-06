package com.unisage.gateway.filter;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.unisage.gateway.security.JwtValidator;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.mock.http.server.reactive.MockServerHttpRequest;
import org.springframework.mock.web.server.MockServerWebExchange;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;

class AuthenticationFilterTest {

    private static final String SECRET = "Unisage_Enterprise_Assistant_Authentication_Secret_Key";
    private static final SecretKey KEY = Keys.hmacShaKeyFor(SECRET.getBytes(StandardCharsets.UTF_8));

    private AuthenticationFilter filter;

    @BeforeEach
    void setUp() {
        JwtValidator jwtValidator = new JwtValidator();
        ReflectionTestUtils.setField(jwtValidator, "jwtSecret", SECRET);
        ReflectionTestUtils.invokeMethod(jwtValidator, "init");
        filter = new AuthenticationFilter(jwtValidator, new ObjectMapper());
    }

    private String validAccessToken() {
        return Jwts.builder()
                .setSubject("user-123")
                .claim("code", "EMP001")
                .claim("role", "ADMIN")
                .claim("type", "access")
                .claim("department_access", List.of("HR", "IT"))
                .claim("permissions", List.of("READ", "WRITE"))
                .setExpiration(new Date(System.currentTimeMillis() + 60_000))
                .signWith(KEY)
                .compact();
    }

    private String expiredAccessToken() {
        return Jwts.builder()
                .setSubject("user-123")
                .claim("type", "access")
                .setExpiration(new Date(System.currentTimeMillis() - 60_000))
                .signWith(KEY)
                .compact();
    }

    /** Captures the exchange the filter forwards downstream, without a real Python/service behind it. */
    private static class CapturingChain implements GatewayFilterChain {
        AtomicReference<ServerWebExchange> captured = new AtomicReference<>();

        @Override
        public Mono<Void> filter(ServerWebExchange exchange) {
            captured.set(exchange);
            return Mono.empty();
        }
    }

    // ---- Optional-auth path: /api/v1/ai/chat/stream ----

    @Test
    void optionalAuthPath_validToken_injectsAllFiveHeadersAndProceeds() {
        MockServerHttpRequest request = MockServerHttpRequest
                .get("/api/v1/ai/chat/stream")
                .header("Authorization", "Bearer " + validAccessToken())
                .build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);
        CapturingChain chain = new CapturingChain();

        filter.filter(exchange, chain).block();

        ServerHttpRequest forwarded = chain.captured.get().getRequest();
        assertThat(forwarded).isNotNull();
        assertThat(forwarded.getHeaders().getFirst("Authorization")).isEqualTo("Bearer " + tokenUsed(forwarded));
        assertThat(forwarded.getHeaders().getFirst("X-User-Department-Access")).isEqualTo("[\"HR\",\"IT\"]");
        assertThat(forwarded.getHeaders().getFirst("X-User-Permissions")).isEqualTo("[\"READ\",\"WRITE\"]");
        assertThat(forwarded.getHeaders().getFirst("X-User-Id")).isEqualTo("user-123");
        assertThat(forwarded.getHeaders().getFirst("X-User-Role")).isEqualTo("ADMIN");
        assertThat(forwarded.getHeaders().getFirst("X-User-Code")).isEqualTo("EMP001");
        assertThat(exchange.getResponse().getStatusCode()).isNull();
    }

    private String tokenUsed(ServerHttpRequest forwarded) {
        String auth = forwarded.getHeaders().getFirst("Authorization");
        return auth.substring("Bearer ".length());
    }

    @Test
    void optionalAuthPath_invalidToken_rejectsWith401() {
        MockServerHttpRequest request = MockServerHttpRequest
                .get("/api/v1/ai/chat/stream")
                .header("Authorization", "Bearer garbage-invalid-token")
                .build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);
        CapturingChain chain = new CapturingChain();

        filter.filter(exchange, chain).block();

        assertThat(exchange.getResponse().getStatusCode()).isEqualTo(org.springframework.http.HttpStatus.UNAUTHORIZED);
        assertThat(chain.captured.get()).isNull();
    }

    @Test
    void optionalAuthPath_expiredToken_rejectsWith401() {
        MockServerHttpRequest request = MockServerHttpRequest
                .get("/api/v1/ai/chat/stream")
                .header("Authorization", "Bearer " + expiredAccessToken())
                .build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);
        CapturingChain chain = new CapturingChain();

        filter.filter(exchange, chain).block();

        assertThat(exchange.getResponse().getStatusCode()).isEqualTo(org.springframework.http.HttpStatus.UNAUTHORIZED);
        assertThat(chain.captured.get()).isNull();
    }

    @Test
    void optionalAuthPath_noToken_proceedsWithNoUserHeaders() {
        MockServerHttpRequest request = MockServerHttpRequest
                .get("/api/v1/ai/chat/stream")
                .build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);
        CapturingChain chain = new CapturingChain();

        filter.filter(exchange, chain).block();

        assertThat(exchange.getResponse().getStatusCode()).isNull();
        ServerHttpRequest forwarded = chain.captured.get().getRequest();
        assertThat(forwarded).isNotNull();
        assertThat(forwarded.getHeaders().getFirst("Authorization")).isNull();
        assertThat(forwarded.getHeaders().getFirst("X-User-Department-Access")).isNull();
        assertThat(forwarded.getHeaders().getFirst("X-User-Permissions")).isNull();
        assertThat(forwarded.getHeaders().getFirst("X-User-Id")).isNull();
        assertThat(forwarded.getHeaders().getFirst("X-User-Role")).isNull();
        assertThat(forwarded.getHeaders().getFirst("X-User-Code")).isNull();
    }

    @Test
    void optionalAuthPath_conversationsCreate_noToken_proceedsWithNoUserHeaders() {
        // POST /conversations must stay reachable by guests - backend-java
        // creates it with ownerId=null (see ConversationController.create).
        MockServerHttpRequest request = MockServerHttpRequest
                .post("/api/v1/master/conversations")
                .build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);
        CapturingChain chain = new CapturingChain();

        filter.filter(exchange, chain).block();

        assertThat(exchange.getResponse().getStatusCode()).isNull();
        assertThat(chain.captured.get()).isNotNull();
    }

    // ---- Existing public path behavior must be unaffected ----

    @Test
    void publicPath_noToken_proceedsWithoutAuth() {
        MockServerHttpRequest request = MockServerHttpRequest
                .post("/api/v1/master/auth/login")
                .build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);
        CapturingChain chain = new CapturingChain();

        filter.filter(exchange, chain).block();

        assertThat(exchange.getResponse().getStatusCode()).isNull();
        assertThat(chain.captured.get()).isNotNull();
    }

    // ---- Existing private-path behavior must be unaffected, plus gains the 3 new headers ----

    @Test
    void privatePath_noToken_rejectsWith401() {
        MockServerHttpRequest request = MockServerHttpRequest
                .get("/api/v1/master/users/me")
                .build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);
        CapturingChain chain = new CapturingChain();

        filter.filter(exchange, chain).block();

        assertThat(exchange.getResponse().getStatusCode()).isEqualTo(org.springframework.http.HttpStatus.UNAUTHORIZED);
        assertThat(chain.captured.get()).isNull();
    }

    @Test
    void privatePath_invalidToken_rejectsWith401() {
        MockServerHttpRequest request = MockServerHttpRequest
                .get("/api/v1/master/users/me")
                .header("Authorization", "Bearer garbage-invalid-token")
                .build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);
        CapturingChain chain = new CapturingChain();

        filter.filter(exchange, chain).block();

        assertThat(exchange.getResponse().getStatusCode()).isEqualTo(org.springframework.http.HttpStatus.UNAUTHORIZED);
    }

    @Test
    void privatePath_validToken_injectsAllFiveHeaders() {
        MockServerHttpRequest request = MockServerHttpRequest
                .get("/api/v1/master/users/me")
                .header("Authorization", "Bearer " + validAccessToken())
                .build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);
        CapturingChain chain = new CapturingChain();

        filter.filter(exchange, chain).block();

        ServerHttpRequest forwarded = chain.captured.get().getRequest();
        assertThat(forwarded.getHeaders().getFirst("X-User-Department-Access")).isEqualTo("[\"HR\",\"IT\"]");
        assertThat(forwarded.getHeaders().getFirst("X-User-Permissions")).isEqualTo("[\"READ\",\"WRITE\"]");
        assertThat(forwarded.getHeaders().getFirst("X-User-Id")).isEqualTo("user-123");
        assertThat(forwarded.getHeaders().getFirst("X-User-Role")).isEqualTo("ADMIN");
        assertThat(forwarded.getHeaders().getFirst("X-User-Code")).isEqualTo("EMP001");
    }
}

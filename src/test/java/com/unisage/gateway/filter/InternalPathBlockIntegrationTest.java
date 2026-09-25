package com.unisage.gateway.filter;

import java.io.IOException;
import java.net.URI;
import java.util.Date;
import java.util.stream.Stream;

import javax.crypto.SecretKey;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.reactive.server.WebTestClient;

import java.nio.charset.StandardCharsets;

/**
 * Real filter chain, real routing, backend replaced by a MockWebServer. Its own context +
 * MockWebServer so the "0 requests reached the backend" assertion is never polluted by control
 * cases in another test class.
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class InternalPathBlockIntegrationTest {

    private static final String SECRET = "Unisage_Enterprise_Assistant_Authentication_Secret_Key";
    private static final SecretKey KEY = Keys.hmacShaKeyFor(SECRET.getBytes(StandardCharsets.UTF_8));

    private static MockWebServer blockedBackend;

    @DynamicPropertySource
    static void backendUri(DynamicPropertyRegistry registry) throws IOException {
        blockedBackend = new MockWebServer();
        blockedBackend.start();
        String url = blockedBackend.url("/").toString();
        registry.add("JAVA_BACKEND_URI", () -> url.substring(0, url.length() - 1));
        registry.add("PYTHON_AI_URI", () -> url.substring(0, url.length() - 1));
    }

    private final WebTestClient webTestClient = WebTestClient.bindToServer().build();

    @AfterAll
    static void tearDown() throws IOException {
        blockedBackend.shutdown();
    }

    private String validAccessToken() {
        return Jwts.builder()
                .setSubject("user-123")
                .claim("type", "access")
                .setExpiration(new Date(System.currentTimeMillis() + 60_000))
                .signWith(KEY)
                .compact();
    }

    static Stream<Arguments> guardedPaths() {
        return Stream.of(
                "/api/v1/master/internal/model-registry/snapshot",
                "/api/v1/master/internal/model-registry/verifications/claim",
                "/api/v1/master/internal/model-registry/embedding-index/unisage_chunks/identity",
                "/api/v1/ai/internal/whatever",
                "/api/v1/master/INTERNAL/model-registry/snapshot",
                "/api/v1/master/%69nternal/model-registry/snapshot",
                "/api/v1/master//internal/model-registry/snapshot",
                "/api/v1/master/x/../internal/model-registry/snapshot",
                "/api/v1/master/x/%2E%2E/internal/model-registry/snapshot",
                "/api/v1/master/x%2F..%2Finternal/model-registry/snapshot",
                "/api/v1/master/%252E%252E/internal/model-registry/snapshot",
                "/api/v1/master/internal;a=b/model-registry/snapshot",
                "/api/v1/master;x=y/internal/model-registry/snapshot"
        ).map(Arguments::of);
    }

    @ParameterizedTest
    @MethodSource("guardedPaths")
    void noJwt_guardedPath_blockedBefore404_zeroBackendRequests(String rawPath) {
        long before = blockedBackend.getRequestCount();

        webTestClient.get().uri(URI.create("http://localhost:" + port() + rawPath))
                .exchange()
                .expectStatus().isNotFound();

        assertNoNewRequests(before);
    }

    @ParameterizedTest
    @MethodSource("guardedPaths")
    void validJwt_guardedPath_stillBlockedWith404_zeroBackendRequests(String rawPath) {
        long before = blockedBackend.getRequestCount();

        webTestClient.get().uri(URI.create("http://localhost:" + port() + rawPath))
                .header("Authorization", "Bearer " + validAccessToken())
                .exchange()
                .expectStatus().isNotFound();

        assertNoNewRequests(before);
    }

    @Test
    void expiredJwt_guardedPath_stillBlockedWith404() {
        String expired = Jwts.builder()
                .setSubject("user-123")
                .claim("type", "access")
                .setExpiration(new Date(System.currentTimeMillis() - 60_000))
                .signWith(KEY)
                .compact();
        long before = blockedBackend.getRequestCount();

        webTestClient.get().uri(URI.create(
                        "http://localhost:" + port() + "/api/v1/master/internal/model-registry/snapshot"))
                .header("Authorization", "Bearer " + expired)
                .exchange()
                .expectStatus().isNotFound();

        assertNoNewRequests(before);
    }

    private void assertNoNewRequests(long before) {
        long after = blockedBackend.getRequestCount();
        org.assertj.core.api.Assertions.assertThat(after).isEqualTo(before);
    }

    @LocalServerPort
    private int localPort;

    private int port() {
        return localPort;
    }
}

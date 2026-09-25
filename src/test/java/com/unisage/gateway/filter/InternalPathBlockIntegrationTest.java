package com.unisage.gateway.filter;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.Socket;
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

    private String expiredAccessToken() {
        return Jwts.builder()
                .setSubject("user-123")
                .claim("type", "access")
                .setExpiration(new Date(System.currentTimeMillis() - 60_000))
                .signWith(KEY)
                .compact();
    }

    private String tamperedAccessToken() {
        // Valid shape, wrong signing key: exercises the "JWT sai" branch of the matrix distinctly
        // from "hết hạn" (expired) — both must be blocked before the token is even inspected.
        SecretKey wrongKey = Keys.hmacShaKeyFor(
                "a-completely-different-signing-key-not-used-by-gateway".getBytes(StandardCharsets.UTF_8));
        return Jwts.builder()
                .setSubject("user-123")
                .claim("type", "access")
                .setExpiration(new Date(System.currentTimeMillis() + 60_000))
                .signWith(wrongKey)
                .compact();
    }

    @ParameterizedTest
    @MethodSource("guardedPaths")
    void expiredJwt_guardedPath_stillBlockedWith404_zeroBackendRequests(String rawPath) {
        long before = blockedBackend.getRequestCount();

        webTestClient.get().uri(URI.create("http://localhost:" + port() + rawPath))
                .header("Authorization", "Bearer " + expiredAccessToken())
                .exchange()
                .expectStatus().isNotFound();

        assertNoNewRequests(before);
    }

    @ParameterizedTest
    @MethodSource("guardedPaths")
    void invalidSignatureJwt_guardedPath_stillBlockedWith404_zeroBackendRequests(String rawPath) {
        long before = blockedBackend.getRequestCount();

        webTestClient.get().uri(URI.create("http://localhost:" + port() + rawPath))
                .header("Authorization", "Bearer " + tamperedAccessToken())
                .exchange()
                .expectStatus().isNotFound();

        assertNoNewRequests(before);
    }

    @Test
    void noJwt_embeddingIndexIdentity_put_alsoBlockedWith404_zeroBackendRequests() {
        long before = blockedBackend.getRequestCount();

        webTestClient.put().uri(URI.create("http://localhost:" + port()
                        + "/api/v1/master/internal/model-registry/embedding-index/unisage_chunks/identity"))
                .exchange()
                .expectStatus().isNotFound();

        assertNoNewRequests(before);
    }

    @Test
    void validJwt_embeddingIndexIdentity_put_alsoBlockedWith404_zeroBackendRequests() {
        long before = blockedBackend.getRequestCount();

        webTestClient.put().uri(URI.create("http://localhost:" + port()
                        + "/api/v1/master/internal/model-registry/embedding-index/unisage_chunks/identity"))
                .header("Authorization", "Bearer " + validAccessToken())
                .exchange()
                .expectStatus().isNotFound();

        assertNoNewRequests(before);
    }

    /**
     * A raw backslash in the request target is not representable by {@code java.net.URI} (any
     * client built on it, including {@code WebTestClient}, refuses to even construct the
     * request), so this one case is sent over a plain socket with the exact bytes on the request
     * line — the only way to prove the filter (or, if Netty's HTTP decoder rejects the malformed
     * request line first, the server itself) never lets it reach the backend. Per plan.md, a 400
     * from Netty rejecting the request line before the filter runs is accepted here instead of
     * 404, as long as zero bytes reach the backend.
     */
    @Test
    void noJwt_rawBackslashTraversal_rejectedBeforeBackend_400or404() throws IOException {
        long before = blockedBackend.getRequestCount();

        int status = sendRawRequestLine(
                "GET /api/v1/master/x\\..\\internal/model-registry/snapshot HTTP/1.1");

        org.assertj.core.api.Assertions.assertThat(status).isIn(400, 404);
        assertNoNewRequests(before);
    }

    /** Opens a raw socket to the gateway and writes the given request line verbatim, unencoded. */
    private int sendRawRequestLine(String requestLine) throws IOException {
        try (Socket socket = new Socket("localhost", localPort)) {
            socket.setSoTimeout(5000);
            OutputStream out = socket.getOutputStream();
            String request = requestLine + "\r\n"
                    + "Host: localhost:" + localPort + "\r\n"
                    + "Connection: close\r\n"
                    + "\r\n";
            out.write(request.getBytes(StandardCharsets.UTF_8));
            out.flush();

            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8))) {
                String statusLine = reader.readLine();
                if (statusLine == null) {
                    // Connection closed/reset without a response = rejected before any handler ran.
                    return 400;
                }
                String[] parts = statusLine.split(" ");
                return Integer.parseInt(parts[1]);
            }
        } catch (java.net.SocketException e) {
            // Connection reset by peer: Netty tore down the connection instead of responding.
            return 400;
        }
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

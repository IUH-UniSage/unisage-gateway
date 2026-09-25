package com.unisage.gateway.filter;

import java.io.IOException;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.Date;

import javax.crypto.SecretKey;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.reactive.server.WebTestClient;

/**
 * Separate context + separate MockWebServer from InternalPathBlockIntegrationTest, so its own
 * "request reached the backend" assertions can never make that test's "0 requests" flaky.
 * Paths that look similar to /internal/ but aren't must still reach the backend.
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class InternalPathBlockControlTest {

    private static final String SECRET = "Unisage_Enterprise_Assistant_Authentication_Secret_Key";
    private static final SecretKey KEY = Keys.hmacShaKeyFor(SECRET.getBytes(StandardCharsets.UTF_8));

    private static MockWebServer controlBackend;

    @DynamicPropertySource
    static void backendUri(DynamicPropertyRegistry registry) throws IOException {
        controlBackend = new MockWebServer();
        controlBackend.start();
        String url = controlBackend.url("/").toString();
        registry.add("JAVA_BACKEND_URI", () -> url.substring(0, url.length() - 1));
        registry.add("PYTHON_AI_URI", () -> url.substring(0, url.length() - 1));
    }

    @AfterAll
    static void tearDown() throws IOException {
        controlBackend.shutdown();
    }

    private final WebTestClient webTestClient = WebTestClient.bindToServer().build();

    @LocalServerPort
    private int localPort;

    private String validAccessToken() {
        return Jwts.builder()
                .setSubject("user-123")
                .claim("type", "access")
                .setExpiration(new Date(System.currentTimeMillis() + 60_000))
                .signWith(KEY)
                .compact();
    }

    @Test
    void chatModelsPath_reachesBackend_exactlyOnce() {
        controlBackend.enqueue(new MockResponse().setResponseCode(200).setBody("{}"));
        long before = controlBackend.getRequestCount();

        webTestClient.get()
                .uri(URI.create("http://localhost:" + localPort + "/api/v1/master/chat-models"))
                .header("Authorization", "Bearer " + validAccessToken())
                .exchange()
                .expectStatus().isOk();

        org.assertj.core.api.Assertions.assertThat(controlBackend.getRequestCount()).isEqualTo(before + 1);
    }

    @Test
    void internalDocsPath_looksSimilarButIsNotGuarded_reachesBackend() {
        controlBackend.enqueue(new MockResponse().setResponseCode(200).setBody("{}"));
        long before = controlBackend.getRequestCount();

        webTestClient.get()
                .uri(URI.create("http://localhost:" + localPort + "/api/v1/master/internal-docs"))
                .header("Authorization", "Bearer " + validAccessToken())
                .exchange()
                .expectStatus().isOk();

        org.assertj.core.api.Assertions.assertThat(controlBackend.getRequestCount()).isEqualTo(before + 1);
    }
}

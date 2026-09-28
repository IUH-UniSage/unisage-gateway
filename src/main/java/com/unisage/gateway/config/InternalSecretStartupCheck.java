package com.unisage.gateway.config;

import java.net.URI;
import java.util.Set;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;

/** In profile prod, fails startup instead of routing to a dev-only upstream host or default secret. */
@Component
public class InternalSecretStartupCheck {

    private static final String DEFAULT_SECRET = "unisage-internal-secret-key-2026";
    private static final int MIN_SECRET_LENGTH = 32;
    private static final Set<String> DEV_ONLY_HOSTS = Set.of("host.docker.internal", "localhost", "127.0.0.1");

    private final Environment environment;

    public InternalSecretStartupCheck(Environment environment) {
        this.environment = environment;
    }

    @Value("${INTERNAL_SECRET_KEY:unisage-internal-secret-key-2026}")
    private String internalSecretKey;

    @Value("${JAVA_BACKEND_URI:http://localhost:8401}")
    private String javaBackendUri;

    @Value("${PYTHON_AI_URI:http://localhost:8402}")
    private String pythonAiUri;

    @PostConstruct
    void validate() {
        if (!isProdProfile()) {
            return;
        }
        if (internalSecretKey == null || internalSecretKey.equals(DEFAULT_SECRET)
                || internalSecretKey.length() < MIN_SECRET_LENGTH) {
            throw new IllegalStateException(
                    "INTERNAL_SECRET_KEY must be set to a non-default value with at least "
                            + MIN_SECRET_LENGTH + " characters in profile prod");
        }
        requireNonDevHost("JAVA_BACKEND_URI", javaBackendUri);
        requireNonDevHost("PYTHON_AI_URI", pythonAiUri);
    }

    private void requireNonDevHost(String name, String uriValue) {
        String host = URI.create(uriValue).getHost();
        if (host != null && DEV_ONLY_HOSTS.contains(host.toLowerCase(java.util.Locale.ROOT))) {
            throw new IllegalStateException(
                    name + " points at a dev-only host (" + host + ") in profile prod");
        }
    }

    private boolean isProdProfile() {
        for (String profile : environment.getActiveProfiles()) {
            if ("prod".equals(profile)) {
                return true;
            }
        }
        return false;
    }
}

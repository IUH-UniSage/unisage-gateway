package com.unisage.gateway.config;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.core.env.Environment;
import org.springframework.test.util.ReflectionTestUtils;

import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class InternalSecretStartupCheckTest {

    private static final String VALID_SECRET = "a-real-secret-at-least-32-characters-long";
    private static final String DEFAULT_SECRET = "unisage-internal-secret-key-2026";

    private Environment environment;

    @BeforeEach
    void setUp() {
        environment = mock(Environment.class);
    }

    private InternalSecretStartupCheck checkFor(String... activeProfiles) {
        when(environment.getActiveProfiles()).thenReturn(activeProfiles);
        InternalSecretStartupCheck check = new InternalSecretStartupCheck(environment);
        ReflectionTestUtils.setField(check, "internalSecretKey", VALID_SECRET);
        ReflectionTestUtils.setField(check, "javaBackendUri", "http://backend-java:8401");
        ReflectionTestUtils.setField(check, "pythonAiUri", "http://unisage-agent:8402");
        return check;
    }

    @Test
    void nonProdProfile_devHosts_neverFails() {
        InternalSecretStartupCheck check = checkFor("dev");
        ReflectionTestUtils.setField(check, "internalSecretKey", DEFAULT_SECRET);
        ReflectionTestUtils.setField(check, "javaBackendUri", "http://host.docker.internal:8401");

        assertThatCode(() -> ReflectionTestUtils.invokeMethod(check, "validate")).doesNotThrowAnyException();
    }

    @Test
    void prodProfile_defaultSecret_fails() {
        InternalSecretStartupCheck check = checkFor("prod");
        ReflectionTestUtils.setField(check, "internalSecretKey", DEFAULT_SECRET);

        assertThatThrownBy(() -> ReflectionTestUtils.invokeMethod(check, "validate"))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("INTERNAL_SECRET_KEY");
    }

    @Test
    void prodProfile_javaBackendUriHostDockerInternal_fails() {
        InternalSecretStartupCheck check = checkFor("prod");
        ReflectionTestUtils.setField(check, "javaBackendUri", "http://host.docker.internal:8401");

        assertThatThrownBy(() -> ReflectionTestUtils.invokeMethod(check, "validate"))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("JAVA_BACKEND_URI");
    }

    @Test
    void prodProfile_pythonAiUriLocalhost_fails() {
        InternalSecretStartupCheck check = checkFor("prod");
        ReflectionTestUtils.setField(check, "pythonAiUri", "http://localhost:8402");

        assertThatThrownBy(() -> ReflectionTestUtils.invokeMethod(check, "validate"))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("PYTHON_AI_URI");
    }

    @Test
    void prodProfile_validConfig_passes() {
        InternalSecretStartupCheck check = checkFor("prod");

        assertThatCode(() -> ReflectionTestUtils.invokeMethod(check, "validate")).doesNotThrowAnyException();
    }
}

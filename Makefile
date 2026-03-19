ANDROID_IMAGE ?= docstore-android-build:0.1
ANDROID_PROJECT_DIR := /workspace/mobile/android
ANDROID_PLATFORM ?= linux/amd64
ANDROID_RUNNER_NAME ?= docstore-android-run
ANDROID_GRADLE_HOME ?= /tmp/gradle-cache
ANDROID_PROJECT_CACHE ?= /tmp/gradle-project-cache
GRADLE_CMD ?= gradle --no-daemon --project-cache-dir $(ANDROID_PROJECT_CACHE)
ANDROID_STUDIO_JAVA ?= /Applications/Android Studio.app/Contents/jbr/Contents/Home
ANDROID_LOCAL_HOME := $(PWD)/mobile/android/.android-home
ANDROID_LOCAL_USER_HOME := $(PWD)/mobile/android/.android-user
ANDROID_LOCAL_GRADLE_HOME := $(PWD)/mobile/android/.gradle-local
VERSION ?= $(shell sed -n 's/^VERSION=//p' .env 2>/dev/null | head -n1)
ifeq ($(strip $(VERSION)),)
VERSION := $(shell sed -n 's/^VERSION=//p' .env.example 2>/dev/null | head -n1)
endif
ANDROID_DEBUG_APK := mobile/android/app/build/outputs/apk/debug/app-debug.apk
ANDROID_RELEASE_APK := mobile/android/app/build/outputs/apk/release/app-release.apk
ANDROID_PUBLISH_DIR := static/mobile
ANDROID_VERSIONED_APK := $(ANDROID_PUBLISH_DIR)/docstore-mobile-$(VERSION).apk
ANDROID_LATEST_APK := $(ANDROID_PUBLISH_DIR)/docstore-mobile-latest.apk
ANDROID_LATEST_META := $(ANDROID_PUBLISH_DIR)/latest.json
DOCKER_RUN_ANDROID := docker run --rm -t --name $(ANDROID_RUNNER_NAME) --platform $(ANDROID_PLATFORM) \
	-e GRADLE_USER_HOME=$(ANDROID_GRADLE_HOME) \
	-v $(PWD):/workspace \
	-v docstore-android-cache:/opt/android-sdk/.android \
	-w $(ANDROID_PROJECT_DIR) \
	$(ANDROID_IMAGE)
LOCAL_GRADLE_ANDROID = cd mobile/android && mkdir -p .android-home .android-user && JAVA_HOME="$(ANDROID_STUDIO_JAVA)" HOME="$(ANDROID_LOCAL_HOME)" ANDROID_USER_HOME="$(ANDROID_LOCAL_USER_HOME)" GRADLE_USER_HOME="$(ANDROID_LOCAL_GRADLE_HOME)" ./gradlew --no-daemon

.PHONY: help mobile-android-reset mobile-android-image mobile-android-wrapper mobile-android-build mobile-android-build-release mobile-android-publish mobile-android-clean mobile-android-shell

help:
	@printf "Available targets:\n"
	@printf "  make mobile-android-image    Build the reusable Android build container\n"
	@printf "  make mobile-android-wrapper  Generate/update the Gradle wrapper inside mobile/android\n"
	@printf "  make mobile-android-build    Run assembleDebug inside the Android build container\n"
	@printf "  make mobile-android-build-release Run assembleRelease inside the Android build container\n"
	@printf "  make mobile-android-publish  Build release APK and publish it into static/mobile\n"
	@printf "  make mobile-android-clean    Run gradle clean inside the Android build container\n"
	@printf "  make mobile-android-shell    Open a shell inside the Android build container\n"
	@printf "  make mobile-android-reset    Remove stale Android build container/cache locks\n"

mobile-android-reset:
	-docker rm -f $(ANDROID_RUNNER_NAME) >/dev/null 2>&1 || true

mobile-android-image:
	@if docker info >/dev/null 2>&1; then \
		docker build --platform $(ANDROID_PLATFORM) -t $(ANDROID_IMAGE) -f mobile/android/build-support/Dockerfile .; \
	else \
		echo "Docker daemon not available; using local Android toolchain fallback."; \
	fi

mobile-android-wrapper: mobile-android-reset mobile-android-image
	@if docker info >/dev/null 2>&1; then \
		$(DOCKER_RUN_ANDROID) $(GRADLE_CMD) wrapper --gradle-version 8.9; \
	else \
		$(LOCAL_GRADLE_ANDROID) wrapper --gradle-version 8.9; \
	fi

mobile-android-build: mobile-android-reset mobile-android-image
	@if docker info >/dev/null 2>&1; then \
		$(DOCKER_RUN_ANDROID) $(GRADLE_CMD) assembleDebug; \
	else \
		$(LOCAL_GRADLE_ANDROID) assembleDebug; \
	fi

mobile-android-build-release: mobile-android-reset mobile-android-image
	@if docker info >/dev/null 2>&1; then \
		$(DOCKER_RUN_ANDROID) $(GRADLE_CMD) assembleRelease; \
	else \
		$(LOCAL_GRADLE_ANDROID) assembleRelease; \
	fi

mobile-android-publish: mobile-android-build-release
	@mkdir -p $(ANDROID_PUBLISH_DIR)
	@rm -f $(ANDROID_PUBLISH_DIR)/*.apk $(ANDROID_LATEST_META)
	@cp $(ANDROID_RELEASE_APK) $(ANDROID_VERSIONED_APK)
	@cp $(ANDROID_RELEASE_APK) $(ANDROID_LATEST_APK)
	@printf '{\n  "version": "%s",\n  "download_path": "/mobile/docstore-mobile-latest.apk",\n  "versioned_path": "/mobile/docstore-mobile-%s.apk"\n}\n' "$(VERSION)" "$(VERSION)" > $(ANDROID_LATEST_META)
	@printf "Published Android APK: %s\n" "$(ANDROID_VERSIONED_APK)"

mobile-android-clean: mobile-android-reset mobile-android-image
	@if docker info >/dev/null 2>&1; then \
		$(DOCKER_RUN_ANDROID) $(GRADLE_CMD) clean; \
	else \
		$(LOCAL_GRADLE_ANDROID) clean; \
	fi

mobile-android-shell: mobile-android-reset mobile-android-image
	@if docker info >/dev/null 2>&1; then \
		$(DOCKER_RUN_ANDROID) bash; \
	else \
		echo "Docker daemon is not running; use Android Studio or local Gradle instead."; \
		exit 1; \
	fi

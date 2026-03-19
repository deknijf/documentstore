FROM eclipse-temurin:17-jdk-jammy

ARG DEBIAN_FRONTEND=noninteractive
ARG GRADLE_VERSION=8.9
ARG ANDROID_CMDLINE_TOOLS_VERSION=11076708
ARG ANDROID_PLATFORM=android-35
ARG ANDROID_BUILD_TOOLS=35.0.0

ENV ANDROID_SDK_ROOT=/opt/android-sdk
ENV ANDROID_HOME=/opt/android-sdk
ENV GRADLE_HOME=/opt/gradle
ENV PATH=$PATH:/opt/gradle/bin:/opt/android-sdk/cmdline-tools/latest/bin:/opt/android-sdk/platform-tools

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    git \
    ca-certificates \
    libstdc++6 \
    libgcc-s1 \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip -O /tmp/gradle.zip \
    && unzip -q /tmp/gradle.zip -d /opt \
    && mv /opt/gradle-${GRADLE_VERSION} /opt/gradle \
    && rm /tmp/gradle.zip

RUN mkdir -p ${ANDROID_SDK_ROOT}/cmdline-tools \
    && wget -q https://dl.google.com/android/repository/commandlinetools-linux-${ANDROID_CMDLINE_TOOLS_VERSION}_latest.zip -O /tmp/android-tools.zip \
    && unzip -q /tmp/android-tools.zip -d ${ANDROID_SDK_ROOT}/cmdline-tools \
    && mv ${ANDROID_SDK_ROOT}/cmdline-tools/cmdline-tools ${ANDROID_SDK_ROOT}/cmdline-tools/latest \
    && rm /tmp/android-tools.zip

RUN yes | sdkmanager --licenses >/dev/null \
    && sdkmanager \
        "platform-tools" \
        "platforms;${ANDROID_PLATFORM}" \
        "build-tools;${ANDROID_BUILD_TOOLS}"

WORKDIR /workspace/mobile/android

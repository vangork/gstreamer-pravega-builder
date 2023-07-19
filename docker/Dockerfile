ARG BASE_IMAGE=ubuntu:20.04

# Build image with Rust compiler.
FROM ${BASE_IMAGE} as builder
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=GMT
RUN apt-get update && \
    apt-get install -y wget git build-essential pkg-config \
    libglib2.0-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstrtspserver-1.0-dev

ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH \
    RUST_VERSION=1.63.0
RUN set -eux; \
    rustArch="x86_64-unknown-linux-gnu"; \
    url="https://static.rust-lang.org/rustup/archive/1.25.1/${rustArch}/rustup-init"; \
    wget --quiet "$url"; \
    chmod +x rustup-init; \
    ./rustup-init -y --no-modify-path --default-toolchain $RUST_VERSION --default-host ${rustArch}; \
    rm rustup-init; \
    chmod -R a+w $RUSTUP_HOME $CARGO_HOME; \
    rustup --version; \
    cargo --version; \
    rustc --version;

WORKDIR /root
ARG RUST_JOBS=1
RUN git clone --recursive https://github.com/pravega/gstreamer-pravega; \
    cd gstreamer-pravega && \
    cargo build --package gst-plugin-pravega --locked --release --jobs ${RUST_JOBS} && \
    cargo build --package pravega_protocol_adapter --locked --release --jobs ${RUST_JOBS}


FROM ${BASE_IMAGE} as prod
USER root

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=GMT
RUN apt-get update && \
    apt-get install -y gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav libgstrtspserver-1.0-0 \
    python3-pip python-gi-dev python3 python3-gi python3-gi-cairo libgstreamer-plugins-base1.0-dev

COPY --from=builder /root/gstreamer-pravega/target/release/libgstpravega.so /usr/lib/x86_64-linux-gnu/gstreamer-1.0/
WORKDIR /opt


COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY inference.py inference.py

COPY docker/entrypoint.sh /entrypoint.sh
CMD ["/entrypoint.sh"]

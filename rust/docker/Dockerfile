FROM rust:1.96-bookworm AS build
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src ./src
RUN cargo build --release --locked

FROM debian:bookworm-slim
COPY --from=build /app/target/release/portzero-rust-docker-example /usr/local/bin/portzero-rust-docker-example
EXPOSE 8080
CMD ["portzero-rust-docker-example"]

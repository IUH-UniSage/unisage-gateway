# API Gateway

Spring Cloud Gateway đứng trước 2 service backend, chịu trách nhiệm xác thực JWT và route request:

| Route prefix (client gọi vào)   | Forward tới                          |
|----------------------------------|---------------------------------------|
| `/api/v1/master/**`             | `backend-java` (`JAVA_BACKEND_URI`)   |
| `/api/v1/ai/**`                 | `backend-py` (`PYTHON_AI_URI`), tự gắn header `X-Internal-Secret` |

Mặc định chạy ở cổng **8400**.

`/api/v1/master/auth/**` và `/api/v1/ai/chat/stream` là public (không cần Bearer token), các route còn lại yêu cầu `Authorization: Bearer <accessToken>`.

## Cấu hình môi trường

Copy `.env.example` thành `.ENV` rồi chỉnh giá trị cho phù hợp:

```bash
cp .env.example .ENV
```

| Biến                  | Ý nghĩa                                                                 |
|------------------------|--------------------------------------------------------------------------|
| `SERVER_PORT`          | Cổng gateway lắng nghe (mặc định `8400`)                                 |
| `JAVA_BACKEND_URI`     | URL tới backend-java. Nếu gateway chạy Docker/devcontainer, dùng `host.docker.internal` thay vì `localhost` để reach được host |
| `PYTHON_AI_URI`        | URL tới backend-py, tương tự lưu ý trên                                  |
| `JWT_SECRET`           | Phải khớp với `JWT_SECRET` của backend-java                              |
| `INTERNAL_SECRET_KEY`  | Phải khớp với `INTERNAL_SECRET_KEY` của backend-py                       |

## Chạy bằng IDE

```bash
./mvnw spring-boot:run
```

## Chạy bằng Docker

```bash
./mvnw clean package -DskipTests
docker compose up -d --build
```

## Chạy bằng Dev Container (VS Code)

Mở thư mục này bằng "Reopen in Container". `postCreateCommand` chỉ tải dependency, **không tự chạy app** — sau khi container mở xong, chạy thủ công:

```bash
sh ./mvnw spring-boot:run
```

Vì gateway cần gọi được backend-java và backend-py, đảm bảo cả hai đang chạy (devcontainer riêng hoặc chạy trực tiếp trên host) và cổng của chúng đã được publish ra `localhost` trước khi test qua gateway.

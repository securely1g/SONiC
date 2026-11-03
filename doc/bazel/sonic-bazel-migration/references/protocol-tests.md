# Minimal generated-protocol consumer tests

Define [generated libraries](code-generation-examples.md) first. Tests share their package, target platform and dependency versions. Execute only original languages/features: message round trips, and RPC only for original services. Reuse assertions on installed copies. These native tests are migration outputs, not regressions in this skill repository. Expectations come from serialization field preservation, Echo behavior and IDL constants. Empty and two nonempty values distinguish defaults and erroneous constant replies.

## 1. protobuf message round trips

### C++

For code-generation.md :message, create message_test.cc:

```cpp
#include "message.pb.h"
#include <string>
#include <initializer_list>
int main() {
    for (const std::string value : {"", "hello", "world"}) {
        Example source;
        source.set_value(value);
        std::string bytes;
        if (!source.SerializeToString(&bytes)) return 1;
        Example restored;
        if (!restored.ParseFromString(bytes)) return 2;
        if (restored.value() != value) return 3;
    }
    return 0;
}
```

```starlark
load("@rules_cc//cc:cc_test.bzl", "cc_test")
cc_test(name = "message_test", srcs = ["message_test.cc"], deps = [":message"])
```

### Python

For :message_python, message_test.py:

```python
import unittest
import message_pb2

class MessageTest(unittest.TestCase):
    def test_roundtrip(self):
        for value in ("", "hello", "world"):
            source = message_pb2.Example(value=value)
            restored = message_pb2.Example.FromString(source.SerializeToString())
            self.assertEqual(restored.value, value)

if __name__ == "__main__":
    unittest.main()
```

```starlark
load("@rules_python//python:py_test.bzl", "py_test")
py_test(name = "message_test", srcs = ["message_test.py"], deps = [":message_python"])
```

### Go

For go.md :message_go, Example additionally declares go_package example.invalid/service/api. message_test.go:

```go
package api
import (
    "testing"
    "google.golang.org/protobuf/proto"
)
func TestRoundtrip(t *testing.T) {
    for _, value := range []string{"", "hello", "world"} {
        data, err := proto.Marshal(&Example{Value: value})
        if err != nil { t.Fatal(err) }
        var restored Example
        if err := proto.Unmarshal(data, &restored); err != nil { t.Fatal(err) }
        if restored.Value != value { t.Fatalf("value = %q, want %q", restored.Value, value) }
    }
}
```

```starlark
load("@io_bazel_rules_go//go:def.bzl", "go_test")
go_test(
    name = "message_test",
    srcs = ["message_test.go"],
    embed = [":message_go"],
    deps = ["//deps:protobuf_go"],
)
```

Caller //deps:protobuf_go aliases google.golang.org/protobuf/proto from the same generated/locked graph.

## 2. gRPC requests and responses

Use echo.proto/echo_cpp/echo_python. Put language examples in their own packages; distinct C++/Python test names also permit shared packages. Bind dynamic localhost ports and assert responses preserve requests.

### C++

echo_test.cc:

```cpp
#include "echo.grpc.pb.h"
#include <grpcpp/grpcpp.h>
#include <chrono>
#include <memory>
#include <string>
#include <initializer_list>
class EchoService final : public demo::Echo::Service {
    grpc::Status Ping(grpc::ServerContext*, const demo::Request* request,
                      demo::Reply* reply) override {
        reply->set_value(request->value());
        return grpc::Status::OK;
    }
};
int main() {
    EchoService service;
    grpc::ServerBuilder builder;
    int port = 0;
    builder.AddListeningPort("127.0.0.1:0", grpc::InsecureServerCredentials(), &port);
    builder.RegisterService(&service);
    auto server = builder.BuildAndStart();
    if (!server || !port) return 1;
    auto stub = demo::Echo::NewStub(grpc::CreateChannel(
        "127.0.0.1:" + std::to_string(port), grpc::InsecureChannelCredentials()));
    int result = 0;
    for (const std::string value : {"", "hello", "world"}) {
        grpc::ClientContext context;
        context.set_deadline(std::chrono::system_clock::now() + std::chrono::seconds(10));
        demo::Request request;
        request.set_value(value);
        demo::Reply reply;
        auto status = stub->Ping(&context, request, &reply);
        if (!status.ok() || reply.value() != value) { result = 2; break; }
    }
    server->Shutdown();
    return result;
}
```

```starlark
load("@rules_cc//cc:cc_test.bzl", "cc_test")
cc_test(name = "echo_cpp_test", srcs = ["echo_test.cc"], deps = [":echo_cpp", "//deps:grpc_cpp"])
```

### Python

echo_test.py:

```python
from concurrent import futures
import unittest
import grpc
import echo_pb2
import echo_pb2_grpc

class Echo(echo_pb2_grpc.EchoServicer):
    def Ping(self, request, context):
        return echo_pb2.Reply(value=request.value)

class EchoTest(unittest.TestCase):
    def test_rpc(self):
        with futures.ThreadPoolExecutor(max_workers=1) as executor:
            server = grpc.server(executor)
            echo_pb2_grpc.add_EchoServicer_to_server(Echo(), server)
            port = server.add_insecure_port("127.0.0.1:0")
            self.assertGreater(port, 0)
            server.start()
            try:
                with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
                    for value in ("", "hello", "world"):
                        reply = echo_pb2_grpc.EchoStub(channel).Ping(
                            echo_pb2.Request(value=value), timeout=10)
                        self.assertEqual(reply.value, value)
            finally:
                server.stop(0).wait()

if __name__ == "__main__":
    unittest.main()
```

```starlark
load("@rules_python//python:py_test.bzl", "py_test")
py_test(name = "echo_python_test", srcs = ["echo_test.py"], deps = [":echo_python", "//deps:grpc_python"])
```

### Go

Add go_package example.invalid/service/rpc and define service_go through the Go proto/gRPC route. echo_test.go:

```go
package rpc
import (
    "context"
    "net"
    "testing"
    "time"
    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials/insecure"
)
type echoServer struct { UnimplementedEchoServer }
func (echoServer) Ping(ctx context.Context, request *Request) (*Reply, error) {
    return &Reply{Value: request.Value}, nil
}
func TestEcho(t *testing.T) {
    listener, err := net.Listen("tcp", "127.0.0.1:0")
    if err != nil { t.Fatal(err) }
    server := grpc.NewServer()
    RegisterEchoServer(server, echoServer{})
    go server.Serve(listener)
    defer server.Stop()
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()
    connection, err := grpc.DialContext(ctx, listener.Addr().String(),
        grpc.WithTransportCredentials(insecure.NewCredentials()), grpc.WithBlock())
    if err != nil { t.Fatal(err) }
    defer connection.Close()
    for _, value := range []string{"", "hello", "world"} {
        reply, err := NewEchoClient(connection).Ping(ctx, &Request{Value: value})
        if err != nil { t.Fatal(err) }
        if reply.Value != value { t.Fatalf("value = %q, want %q", reply.Value, value) }
    }
}
```

```starlark
load("@io_bazel_rules_go//go:def.bzl", "go_test")
go_test(
    name = "echo_go_test",
    srcs = ["echo_test.go"],
    embed = [":service_go"],
    deps = ["//deps:grpc_go", "//deps:grpc_go_insecure"],
)
```

grpc_go/grpc_go_insecure aliases point to grpc and credentials/insecure in one locked graph. DialContext has a deadline; 10 seconds is this example's timeout only.

## 3. Thrift messages and constants

Use message.thrift and its three language libraries. No service exists here, so check fields/constants; real service components use generated Client/Processor and declared transports for request/response checks.

### C++

message_test.cc:

```cpp
#include "message_types.h"
#include "message_constants.h"
#include <thrift/protocol/TBinaryProtocol.h>
#include <thrift/transport/TBufferTransports.h>
#include <memory>
#include <string>
#include <initializer_list>
int main() {
    for (const std::string value : {"", "hello", "world"}) {
        auto transport = std::make_shared<apache::thrift::transport::TMemoryBuffer>();
        apache::thrift::protocol::TBinaryProtocol protocol(transport);
        demo::Message source;
        source.__set_value(value);
        source.write(&protocol);
        demo::Message restored;
        restored.read(&protocol);
        if (restored.value != value) return 1;
    }
    return demo::g_message_constants.ANSWER == 37 ? 0 : 2;
}
```

```starlark
load("@rules_cc//cc:cc_test.bzl", "cc_test")
cc_test(name = "message_test", srcs = ["message_test.cc"], deps = [":message_cpp", "//deps:thrift_cpp"])
```

### Python

message_test.py:

```python
import unittest
from thrift import TSerialization
from demo.ttypes import Message
from demo.constants import ANSWER

class MessageTest(unittest.TestCase):
    def test_roundtrip(self):
        for value in ("", "hello", "world"):
            source = Message(value=value)
            restored = Message()
            TSerialization.deserialize(restored, TSerialization.serialize(source))
            self.assertEqual(restored.value, value)
        self.assertEqual(ANSWER, 37)

if __name__ == "__main__":
    unittest.main()
```

```starlark
load("@rules_python//python:py_test.bzl", "py_test")
py_test(name = "message_test", srcs = ["message_test.py"], deps = [":message_python", "//deps:thrift_python"])
```

### Go

message_test.go:

```go
package demo
import (
    "context"
    "testing"
    "github.com/apache/thrift/lib/go/thrift"
)
func TestRoundtrip(t *testing.T) {
    ctx := context.Background()
    for _, value := range []string{"", "hello", "world"} {
        bytes, err := thrift.NewTSerializer().Write(ctx, &Message{Value: value})
        if err != nil { t.Fatal(err) }
        var restored Message
        if err := thrift.NewTDeserializer().Read(ctx, &restored, bytes); err != nil { t.Fatal(err) }
        if restored.Value != value { t.Fatalf("value = %q, want %q", restored.Value, value) }
    }
    if ANSWER != 37 { t.Fatalf("ANSWER = %d", ANSWER) }
}
```

```starlark
load("@io_bazel_rules_go//go:def.bzl", "go_test")
go_test(name = "message_test", srcs = ["message_test.go"], embed = [":message_go"], deps = ["//deps:thrift_go"])
```

## 4. Execute and record

After completing each example, run its package commands:

```sh
bazel test //proto_example:message_test
bazel test //grpc_example:echo_cpp_test //grpc_example:echo_python_test
bazel test //grpc_go_example:echo_go_test
bazel test //thrift_example:message_test
```

Replace example package names. Same-named message tests remain in separate packages. Preserve first failures or successful platform/tool/artifact identities. Extract installation TARs and repeat behavior in matching environments, checking paths/runtime dependencies. Tests remain validation inputs unless the original delivery installs them.

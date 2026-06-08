const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    // 1. Smoke test executable
    const exe = b.addExecutable(.{
        .name = "vault-zig-smoke-test",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/main.zig"),
            .target = target,
            .optimize = optimize,
            .link_libc = true,
        }),
    });
    exe.root_module.linkSystemLibrary("sqlite3", .{});
    b.installArtifact(exe);

    const run_cmd = b.addRunArtifact(exe);
    run_cmd.step.dependOn(b.getInstallStep());
    if (b.args) |args| {
        run_cmd.addArgs(args);
    }
    const run_step = b.step("run", "Run the app");
    run_step.dependOn(&run_cmd.step);

    // 2. Unit tests
    const exe_unit_tests = b.addTest(.{
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/root.zig"),
            .target = target,
            .optimize = optimize,
            .link_libc = true,
        }),
    });
    exe_unit_tests.root_module.linkSystemLibrary("sqlite3", .{});

    const run_exe_unit_tests = b.addRunArtifact(exe_unit_tests);
    const test_step = b.step("test", "Run unit tests");
    test_step.dependOn(&run_exe_unit_tests.step);

    // 3. Vector runner
    const vectors_exe = b.addExecutable(.{
        .name = "vault-zig-vectors",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/vectors.zig"),
            .target = target,
            .optimize = optimize,
            .link_libc = true,
        }),
    });

    const run_vectors_cmd = b.addRunArtifact(vectors_exe);
    run_vectors_cmd.step.dependOn(&vectors_exe.step);

    // Set CWD for the runner so it can find test-vectors/ relative to repo root
    run_vectors_cmd.cwd = b.path("..");

    const vectors_step = b.step("vectors", "Run shared test vectors");
    vectors_step.dependOn(&run_vectors_cmd.step);
}

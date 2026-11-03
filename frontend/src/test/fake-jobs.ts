import type { Job, JobCreate, JobOptions } from "@/features/downloads/types";
import { type FakeServer, type Route, json, noContent } from "@/test/fake-http";
import { broadcast } from "@/test/fake-socket";

export function makeJob(overrides: Partial<Job> = {}): Job {
  return {
    id: 1,
    url: "https://example.com/watch/abc",
    status: "queued",
    kind: "download",
    scheduled_at: null,
    record_from_start: true,
    part_seconds: null,
    max_seconds: null,
    part: null,
    options: {},
    extra_args: "",
    output_dir: "/downloads",
    folders: null,
    file_name: null,
    media_files: false,
    cookie_id: null,
    proxy_mode: "off",
    proxy_id: null,
    subscription_id: null,
    title: null,
    progress: null,
    downloaded_bytes: null,
    total_bytes: null,
    speed: null,
    eta: null,
    filepath: null,
    keep: false,
    vod_after_seconds: null,
    vod_replace: false,
    source_job_id: null,
    error: null,
    created_at: "2026-10-30T10:00:00+00:00",
    started_at: null,
    finished_at: null,
    revision: 0,
    ...overrides,
  };
}

function findJob(server: FakeServer, params: string[]) {
  return server.jobs.find((job) => job.id === Number(params[0]));
}

function updateJob(server: FakeServer, params: string[], changes: Partial<Job>) {
  const job = findJob(server, params);
  if (!job) {
    return json({ detail: "Download not found" }, 404);
  }
  Object.assign(job, changes, { revision: job.revision + 1 });
  broadcast({ type: "job", job: { ...job } });
  return json(job);
}

function recordingFields(recording: JobCreate["recording"]): Partial<Job> {
  if (!recording) {
    return {};
  }
  const scheduledAt = recording.starts_at ?? null;
  return {
    kind: "live",
    status: scheduledAt ? "scheduled" : "queued",
    scheduled_at: scheduledAt,
    record_from_start: recording.from_start,
    part_seconds: recording.part_hours ? recording.part_hours * 3600 : null,
    max_seconds: recording.max_hours ? recording.max_hours * 3600 : null,
  };
}

function settingsFields(body: Record<string, unknown>): Partial<Job> {
  return {
    options: (body.options as JobOptions | undefined) ?? {},
    extra_args: String(body.extra_args ?? ""),
    output_dir: (body.output_dir as string | null) ?? "/downloads",
    cookie_id: (body.cookie_id as number | null | undefined) ?? null,
    folders: (body.folders as Job["folders"] | undefined) ?? null,
    file_name: (body.file_name as Job["file_name"] | undefined) ?? null,
    media_files: (body.media_files as boolean | undefined) ?? false,
    proxy_mode: (body.proxy_mode as Job["proxy_mode"] | undefined) ?? "off",
  };
}

function createJob(server: FakeServer, body: Record<string, unknown>) {
  const url = String(body.url ?? "");
  if (!/^https?:\/\//.test(url)) {
    const msg = "Value error, Enter a web address starting with http:// or https://";
    return json({ detail: [{ msg }] }, 422);
  }
  if (String(body.extra_args ?? "").includes("--exec")) {
    return json({ detail: "--exec isn't allowed. It runs shell commands." }, 422);
  }
  const job = makeJob({
    id: server.nextJobId,
    url,
    title: (body.title as string | null | undefined) ?? null,
    ...settingsFields(body),
    ...recordingFields(body.recording as JobCreate["recording"]),
  });
  server.nextJobId += 1;
  server.jobs.push(job);
  broadcast({ type: "job", job: { ...job } });
  return json(job, 201);
}

const JOB_PATH = /^\/api\/jobs\/(\d+)$/;

export const jobRoutes: Route[] = [
  {
    method: "GET",
    path: /^\/api\/jobs$/,
    handle: (server, { query }) => {
      const subscription = query.get("subscription_id");
      const jobs = subscription
        ? server.jobs.filter((job) => job.subscription_id === Number(subscription))
        : server.jobs;
      return json(jobs.toSorted((a, b) => b.id - a.id));
    },
  },
  { method: "POST", path: /^\/api\/jobs$/, handle: (server, { body }) => createJob(server, body) },
  {
    method: "POST",
    path: /^\/api\/jobs\/(\d+)\/cancel$/,
    handle: (server, { params }) => updateJob(server, params, { status: "cancelled" }),
  },
  {
    method: "POST",
    path: /^\/api\/jobs\/(\d+)\/retry$/,
    handle: (server, { params }) => updateJob(server, params, { status: "queued", error: null }),
  },
  {
    method: "PUT",
    path: /^\/api\/jobs\/(\d+)\/keep$/,
    handle: (server, { params, body }) =>
      updateJob(server, params, { keep: (body as { keep: boolean }).keep }),
  },
  {
    method: "DELETE",
    path: JOB_PATH,
    handle: (server, { params, query }) => {
      if (query.get("delete_files") === "true") {
        server.deletedJobFiles.push(Number(params[0]));
      }
      server.jobs = server.jobs.filter((job) => job.id !== Number(params[0]));
      broadcast({ type: "job_deleted", id: Number(params[0]) });
      return noContent();
    },
  },
  {
    method: "GET",
    path: /^\/api\/jobs\/(\d+)\/log$/,
    handle: (server, { params }) =>
      new Response(server.logs[Number(params[0])] ?? "", {
        headers: { "Content-Type": "text/plain" },
      }),
  },
  { method: "GET", path: /^\/api\/system$/, handle: (server) => json(server.system) },
];

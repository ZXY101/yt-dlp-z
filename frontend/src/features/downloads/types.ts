import type { components } from "@/api/generated/schema";

export type Job = components["schemas"]["JobOut"];
export type JobCreate = components["schemas"]["JobCreate"];
export type JobStatus = Job["status"];
export type JobOptions = NonNullable<JobCreate["options"]>;

/** Messages sent over /api/ws. Not part of the OpenAPI schema, so typed here. */
export type JobEvent = { type: "job"; job: Job } | { type: "job_deleted"; id: number };
export type MediaInfo = components["schemas"]["MediaInfo"];
export type MediaProbeRequest = components["schemas"]["MediaProbeRequest"];

// Everything that can go wrong talking to the server, each with a message a user can act on.

export type Problem =
  | "not-set-up"
  | "no-permission"
  | "unreachable"
  | "timeout"
  | "needs-token"
  | "bad-token"
  | "send-only"
  | "login-page"
  | "too-old"
  | "rejected"
  | "server-error";

export class ServerProblem extends Error {
  readonly problem: Problem;

  constructor(problem: Problem, message: string) {
    super(message);
    this.name = "ServerProblem";
    this.problem = problem;
  }
}

// Problems fixed on the options page rather than by trying again.
const SETUP_PROBLEMS = new Set<Problem>([
  "not-set-up",
  "no-permission",
  "needs-token",
  "bad-token",
  "login-page",
]);

export function needsSetup(problem: Problem): boolean {
  return SETUP_PROBLEMS.has(problem);
}

export function asServerProblem(error: unknown): ServerProblem {
  if (error instanceof ServerProblem) return error;
  const message = error instanceof Error ? error.message : String(error);
  return new ServerProblem("server-error", message);
}

import { ApiError, describeError, errorMessage } from "@/api/errors";

describe("errorMessage", () => {
  it("uses a string detail", () => {
    expect(errorMessage({ detail: "Incorrect password" })).toBe("Incorrect password");
  });

  it("joins validation issues", () => {
    const body = { detail: [{ msg: "Too short." }, { msg: "Missing." }, { loc: [] }] };
    expect(errorMessage(body)).toBe("Too short. Missing.");
  });

  it("drops Pydantic's 'Value error' prefix", () => {
    const body = { detail: [{ msg: "Value error, Enter a web address." }] };
    expect(errorMessage(body)).toBe("Enter a web address.");
  });

  it.each([undefined, null, "text", {}, { detail: 42 }, { detail: [{}] }])(
    "falls back for %j",
    (body) => {
      expect(errorMessage(body)).toMatch(/Something went wrong/);
    },
  );
});

describe("describeError", () => {
  it("uses the message of errors", () => {
    expect(describeError(new ApiError("Nope", 401))).toBe("Nope");
  });

  it("falls back for non-errors", () => {
    expect(describeError("weird")).toMatch(/Something went wrong/);
  });
});

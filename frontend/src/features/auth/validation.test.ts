import { validateSetup } from "@/features/auth/validation";

const valid = {
  password: "long-enough",
  confirmPassword: "long-enough",
  downloadDir: "/downloads",
  needsPassword: true,
};

describe("validateSetup", () => {
  it("accepts valid input", () => {
    expect(validateSetup(valid)).toEqual({});
  });

  it("requires a long enough password", () => {
    expect(validateSetup({ ...valid, password: "short" }).password).toMatch(/at least 8/);
  });

  it("requires matching passwords", () => {
    expect(validateSetup({ ...valid, confirmPassword: "different" }).confirmPassword).toBeTruthy();
  });

  it("skips password checks when no password is needed", () => {
    expect(validateSetup({ ...valid, password: "", needsPassword: false })).toEqual({});
  });

  it.each([
    ["", /Choose/],
    ["relative/path", /full path/],
  ])("rejects download folder %j", (downloadDir, message) => {
    expect(validateSetup({ ...valid, downloadDir }).downloadDir).toMatch(message);
  });

  it("accepts Windows paths", () => {
    expect(validateSetup({ ...valid, downloadDir: "D:\\Videos" })).toEqual({});
  });
});

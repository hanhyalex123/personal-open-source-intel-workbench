import { render, screen } from "@testing-library/react";
import { theme } from "antd";
import { describe, expect, it } from "vitest";

import AppProviders from "../providers/AppProviders";

function TokenProbe() {
  const { token } = theme.useToken();
  return (
    <div>
      <span data-testid="color-primary">{token.colorPrimary}</span>
      <span data-testid="border-radius">{String(token.borderRadius)}</span>
    </div>
  );
}

describe("AppProviders", () => {
  it("provides the shared antd theme tokens", () => {
    render(
      <AppProviders>
        <TokenProbe />
      </AppProviders>,
    );

    expect(screen.getByTestId("color-primary").textContent).toBe("#1677ff");
    expect(Number(screen.getByTestId("border-radius").textContent)).toBeGreaterThan(0);
  });
});

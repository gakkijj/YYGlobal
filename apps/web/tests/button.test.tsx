import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Button } from "@/components/ui/button";

describe("Button", () => {
  it("renders an accessible action", () => {
    render(<Button>保存画像</Button>);
    expect(screen.getByRole("button", { name: "保存画像" })).toBeInTheDocument();
  });
});


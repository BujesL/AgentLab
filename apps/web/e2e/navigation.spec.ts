import { expect, test } from "@playwright/test";

test("home page shows hero and links to the dashboard", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Agent Evaluation Lab" })).toBeVisible();

  await page.getByRole("link", { name: "Ver experimentos" }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
});

test("dashboard renders without the API running (degrades to an error banner)", async ({
  page,
}) => {
  await page.goto("/dashboard");

  await expect(page.getByRole("heading", { name: "AGENT EVALUATION" })).toBeVisible();
  // Without a live API/DB in this environment, the page must still render —
  // either the "no experiments yet" empty state or the connection-error banner,
  // never a crash. This is the regression this test guards against.
  await expect(page.getByText(/Nenhum experimento ainda|Não foi possível conectar/)).toBeVisible();
});

test("trace detail page degrades gracefully for an unknown/unreachable trace id", async ({
  page,
}) => {
  await page.goto("/traces/does-not-exist");

  await expect(page.getByText(/não encontrado|Não foi possível buscar o trace/)).toBeVisible();
});

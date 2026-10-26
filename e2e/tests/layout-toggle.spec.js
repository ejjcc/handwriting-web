const { test, expect, openHome, fillText, useSmallCanvas, expectPreviewImageLoaded } = require("./fixtures");

test.describe("原版编辑器布局", () => {
  test("收起和展开设置栏时保留正文与预览入口", async ({ page }) => {
    await openHome(page);
    await fillText(page, "设置栏收起测试");
    await page.getByTestId("sidebar-toggle-btn").click();
    await expect(page.getByTestId("panel-settings")).toHaveCount(0);
    await expect(page.getByTestId("text-input")).toHaveValue("设置栏收起测试");
    await expect(page.getByTestId("preview-btn")).toBeVisible();
    await page.getByTestId("sidebar-toggle-btn").click();
    await expect(page.getByTestId("panel-settings")).toBeVisible();
    await expect(page.getByTestId("text-input")).toHaveValue("设置栏收起测试");
  });

  test("收起设置栏后仍然能生成预览", async ({ page }) => {
    await openHome(page);
    await useSmallCanvas(page);
    await fillText(page, "收起后生成测试");
    await page.getByTestId("sidebar-toggle-btn").click();
    await page.getByTestId("preview-btn").click();
    await expectPreviewImageLoaded(page);
  });

  test("分页标记生成两张连续排列的预览纸张", async ({ page }) => {
    await openHome(page);
    await useSmallCanvas(page);
    await fillText(page, "第一页\n---\n第二页\n>>>落款");
    await page.getByTestId("full-preview-toggle-btn").click();
    await page.getByTestId("preview-btn").click();
    const images=page.getByTestId("preview-image");
    await expect(images).toHaveCount(2);
    await expect(page.getByTestId("preview-page-label")).toHaveText(["第 1 页 / 共 2 页", "第 2 页 / 共 2 页"]);
    const boxes=await images.evaluateAll(nodes=>nodes.map(node=>node.getBoundingClientRect().top));
    expect(boxes[1]).toBeGreaterThan(boxes[0]);
  });
});

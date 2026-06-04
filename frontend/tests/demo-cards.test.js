import test from "node:test";
import assert from "node:assert/strict";
import { allDemoCards, getAutoDemoScript } from "../src/config/demo-cards.ts";

test("demo cards use image URLs packaged in frontend public demo directory", () => {
  const imageCards = allDemoCards.filter((card) => card.demo_input.image);

  assert.ok(imageCards.length > 0);

  imageCards.forEach((card) => {
    assert.match(card.demo_input.image, /^\/demo\/[\w-]+\.(jpg|jpeg|png|webp)$/i);
  });
});

test("auto demo script contains five stable packaged steps", () => {
  const script = getAutoDemoScript();

  assert.equal(script.length, 5);
  assert.deepEqual(
    script.map((step) => step.id),
    ["opening", "knowledge-base", "planning", "pricing", "detection"]
  );

  script.forEach((step) => {
    if (step.image) {
      assert.match(step.image, /^\/demo\/[\w-]+\.(jpg|jpeg|png|webp)$/i);
    }
  });
});

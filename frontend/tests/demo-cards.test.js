import React from "react";
import test from "node:test";
import assert from "node:assert/strict";
import { renderToStaticMarkup } from "react-dom/server";
import { allDemoCards, getAutoDemoScript } from "../src/config/demo-cards.ts";
import { ChatMessageBubble } from "../src/components/ChatMessageBubble.tsx";

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

test("assistant messages with markdown remnants are rendered as plain text", () => {
  const message = {
    id: "test-message",
    role: "assistant",
    content: "### 诊断结果\n**牛感染**\n- 先隔离\n- 观察症状",
    isStreaming: false,
  };

  const html = renderToStaticMarkup(React.createElement(ChatMessageBubble, { message }));

  assert.match(html, /诊断结果/);
  assert.doesNotMatch(html, /###/);
  assert.doesNotMatch(html, /\*\*牛感染\*\*/);
});

test("assistant messages with glued markdown markers are normalized into readable plain text", () => {
  const message = {
    id: "test-message-2",
    role: "assistant",
    content: "---### 🩺 疾病预测分析#### 可能的疾病1. 牛结节性皮肤病（可能性：75%）- 判断依据：症状描述中“皮肤表面有多个圆形或椭圆形病变、结痂、溃疡样外观、大小不一、主要分布在躯干和臀部”与知识库中牛结节性皮肤病的典型症状高度吻合。2. 牛传染性鼻气管炎（生殖道型）（可能性：15%）- 判断依据：虽然主要症状为生殖道黏膜病变。",
    isStreaming: false,
  };

  const html = renderToStaticMarkup(React.createElement(ChatMessageBubble, { message }));

  assert.match(html, /疾病预测分析/);
  assert.match(html, /可能的疾病/);
  assert.doesNotMatch(html, /---###/);
  assert.doesNotMatch(html, /####可能的疾病/);
});

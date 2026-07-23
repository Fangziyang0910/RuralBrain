"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { normalizeMarkdownForRendering } from "@/utils/markdownCleanup";

interface MarkdownContentProps {
  content: string;
}

export function MarkdownContent({ content }: MarkdownContentProps) {
  const normalizedContent = normalizeMarkdownForRendering(content);

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ children }) => (
          <p className="my-3 text-base text-stone-800 leading-relaxed">
            {children}
          </p>
        ),
        h1: ({ children }) => (
          <h1 className="text-2xl font-bold my-4 text-stone-900 border-b-2 border-stone-200 pb-2">
            {children}
          </h1>
        ),
        h2: ({ children }) => (
          <h2 className="text-xl font-bold my-4 text-stone-900">
            {children}
          </h2>
        ),
        h3: ({ children }) => (
          <h3 className="text-lg font-bold my-3 text-stone-900">
            {children}
          </h3>
        ),
        h4: ({ children }) => (
          <h4 className="text-base font-bold my-3 text-stone-900">
            {children}
          </h4>
        ),
        h5: ({ children }) => (
          <h5 className="text-sm font-bold my-2 text-stone-900">
            {children}
          </h5>
        ),
        h6: ({ children }) => (
          <h6 className="text-xs font-bold my-2 text-stone-900">
            {children}
          </h6>
        ),
        strong: ({ children }) => (
          <strong className="font-bold text-stone-900">
            {children}
          </strong>
        ),
        em: ({ children }) => (
          <em className="italic text-stone-700">
            {children}
          </em>
        ),
        ul: ({ children }) => (
          <ul className="list-disc list-outside space-y-2 my-3 text-base text-stone-800 pl-5">
            {children}
          </ul>
        ),
        ol: ({ children }) => (
          <ol className="list-decimal list-outside space-y-2 my-3 text-base text-stone-800 pl-5">
            {children}
          </ol>
        ),
        li: ({ children }) => (
          <li className="my-1 text-stone-700 leading-relaxed pl-1">
            {children}
          </li>
        ),
        hr: () => (
          <hr className="my-6 border-t-2 border-stone-300" />
        ),
        blockquote: ({ children }) => (
          <blockquote className="border-l-4 border-stone-400 pl-4 py-2 my-4 bg-stone-50 rounded-r text-stone-700 italic">
            {children}
          </blockquote>
        ),
        code: ({ children }) => (
          <code className="bg-stone-100 text-stone-800 px-1.5 py-0.5 rounded text-sm font-mono">
            {children}
          </code>
        ),
        pre: ({ children }) => (
          <pre className="bg-stone-100 p-4 rounded-lg overflow-x-auto my-4 text-sm border border-stone-200">
            {children}
          </pre>
        ),
        a: ({ children, href }) => (
          <a
            href={href}
            className="text-earth-600 hover:text-earth-700 underline underline-offset-2 transition-colors font-medium"
            target="_blank"
            rel="noopener noreferrer"
          >
            {children}
          </a>
        ),
        table: ({ children }) => (
          <div className="overflow-x-auto my-4">
            <table className="min-w-full divide-y divide-stone-200 border border-stone-300">
              {children}
            </table>
          </div>
        ),
        thead: ({ children }) => (
          <thead className="bg-stone-100">
            {children}
          </thead>
        ),
        tbody: ({ children }) => (
          <tbody className="bg-white divide-y divide-stone-200">
            {children}
          </tbody>
        ),
        tr: ({ children }) => (
          <tr>
            {children}
          </tr>
        ),
        th: ({ children }) => (
          <th className="px-4 py-2 text-left text-sm font-bold text-stone-900">
            {children}
          </th>
        ),
        td: ({ children }) => (
          <td className="px-4 py-2 text-sm text-stone-700">
            {children}
          </td>
        ),
      }}
    >
      {normalizedContent}
    </ReactMarkdown>
  );
}

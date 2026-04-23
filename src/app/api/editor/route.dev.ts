import { NextRequest, NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";
import { books, type Book, type Card } from "@/data/books";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const BOOKS_PATH = path.join(process.cwd(), "src", "data", "books.ts");

const FILE_HEADER = `export interface Card {
  id: string;
  front: string;
  zh: string;
  en: string;
}

export interface Lesson {
  id: string;
  title: string;
  cards: Card[];
}

export interface Book {
  id: string;
  title: string;
  icon: string;
  lessons: Lesson[];
}

`;

function serialize(data: Book[]): string {
  const lines: string[] = [];
  lines.push("export const books: Book[] = [");
  for (const book of data) {
    lines.push("  {");
    lines.push(`    id: ${JSON.stringify(book.id)},`);
    lines.push(`    title: ${JSON.stringify(book.title)},`);
    lines.push(`    icon: ${JSON.stringify(book.icon)},`);
    lines.push(`    lessons: [`);
    for (const lesson of book.lessons) {
      lines.push(`      {`);
      lines.push(`        id: ${JSON.stringify(lesson.id)},`);
      lines.push(`        title: ${JSON.stringify(lesson.title)},`);
      lines.push(`        cards: [`);
      for (const card of lesson.cards) {
        lines.push(
          `          { id: ${JSON.stringify(card.id)}, front: ${JSON.stringify(
            card.front
          )}, zh: ${JSON.stringify(card.zh)}, en: ${JSON.stringify(card.en)} },`
        );
      }
      lines.push(`        ],`);
      lines.push(`      },`);
    }
    lines.push(`    ],`);
    lines.push("  },");
  }
  lines.push("];");
  lines.push("");
  return FILE_HEADER + lines.join("\n");
}

// Server-side in-memory state so mutations are visible across requests
// even if Next's dev hot-reload hasn't picked up the file change yet.
// On cold start (or after hot-reload), state is seeded from the imported books.
let state: Book[] | null = null;
function getState(): Book[] {
  if (!state) state = JSON.parse(JSON.stringify(books));
  return state!;
}

function splitLines(text: string): string[] {
  return text
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l.length > 0);
}

function buildCards(front: string, zh: string, en: string): Card[] {
  const fLines = splitLines(front);
  const zLines = splitLines(zh);
  const eLines = splitLines(en);
  const n = Math.max(fLines.length, zLines.length, eLines.length);
  const cards: Card[] = [];
  for (let i = 0; i < n; i++) {
    cards.push({
      id: `c${i + 1}`,
      front: fLines[i] ?? "",
      zh: zLines[i] ?? "",
      en: eLines[i] ?? "",
    });
  }
  return cards;
}

export async function GET() {
  return NextResponse.json(getState());
}

export async function PUT(req: NextRequest) {
  const body = await req.json();
  const { bookId, lessonId, title, front, zh, en } = body as {
    bookId: string;
    lessonId: string;
    title: string;
    front: string;
    zh: string;
    en: string;
  };

  const data = getState();
  const book = data.find((b) => b.id === bookId);
  if (!book) return NextResponse.json({ error: "book not found" }, { status: 404 });
  const lesson = book.lessons.find((l) => l.id === lessonId);
  if (!lesson) return NextResponse.json({ error: "lesson not found" }, { status: 404 });

  lesson.title = title;
  lesson.cards = buildCards(front, zh, en);

  await fs.writeFile(BOOKS_PATH, serialize(data), "utf8");
  return NextResponse.json({ ok: true, cards: lesson.cards.length });
}

export async function DELETE(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const bookId = searchParams.get("bookId");
  const lessonId = searchParams.get("lessonId");
  if (!bookId || !lessonId) {
    return NextResponse.json({ error: "missing params" }, { status: 400 });
  }

  const data = getState();
  const book = data.find((b) => b.id === bookId);
  if (!book) return NextResponse.json({ error: "book not found" }, { status: 404 });
  const idx = book.lessons.findIndex((l) => l.id === lessonId);
  if (idx === -1) return NextResponse.json({ error: "lesson not found" }, { status: 404 });

  book.lessons.splice(idx, 1);
  await fs.writeFile(BOOKS_PATH, serialize(data), "utf8");
  return NextResponse.json({ ok: true });
}


import { books } from "@/data/books";
import LessonsView from "./view";

export function generateStaticParams() {
  return books.map((b) => ({ bookId: b.id }));
}

export default async function LessonsPage({
  params,
}: {
  params: Promise<{ bookId: string }>;
}) {
  const { bookId } = await params;
  return <LessonsView bookId={bookId} />;
}

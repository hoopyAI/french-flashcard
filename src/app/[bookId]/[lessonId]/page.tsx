import { books } from "@/data/books";
import CardsView from "./view";

export function generateStaticParams() {
  return books.flatMap((b) =>
    b.lessons.map((l) => ({ bookId: b.id, lessonId: l.id }))
  );
}

export default async function CardsPage({
  params,
}: {
  params: Promise<{ bookId: string; lessonId: string }>;
}) {
  const { bookId, lessonId } = await params;
  return <CardsView bookId={bookId} lessonId={lessonId} />;
}

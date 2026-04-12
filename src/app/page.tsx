import Link from "next/link";
import { books } from "@/data/books";

export default function Home() {
  return (
    <div className="p-5 max-w-lg mx-auto">
      <h1 className="text-2xl font-bold mb-5">课文背诵</h1>
      <div className="flex flex-col gap-3">
        {books.map((book) => (
          <Link
            key={book.id}
            href={`/${book.id}`}
            className="card-base flex items-center gap-3 p-4 no-underline text-inherit hover:translate-y-[-2px] transition-transform cursor-pointer"
          >
            <span className="text-3xl">{book.icon}</span>
            <span className="flex-1 text-lg">{book.title}</span>
            <span className="text-sm text-gray-400">
              {book.lessons.length} 课
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}

import { AdminProvider } from "@/context/AdminContext";

export const metadata = {
  title: "LoadMoveGH Admin — Management Console",
  description: "Enterprise admin dashboard for managing the LoadMoveGH freight exchange platform.",
};

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <AdminProvider>{children}</AdminProvider>;
}

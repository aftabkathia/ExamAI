import { redirect } from "next/navigation";

export default function TutorRedirect() {
  redirect("/workspace?tab=chat");
}

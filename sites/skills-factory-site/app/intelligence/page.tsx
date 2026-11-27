import { requireChatGPTUser } from "@/app/chatgpt-auth";
import IntelligenceDashboard from "./ui";

export const dynamic = "force-dynamic";

export default async function IntelligencePage() {
  await requireChatGPTUser("/intelligence");
  return <IntelligenceDashboard />;
}

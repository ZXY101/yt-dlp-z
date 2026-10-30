import { Plus } from "lucide-react";
import { Link } from "react-router";

import { Button } from "@/components/ui/button";

export function NewDownloadButton() {
  return (
    <Button asChild size="lg" className="h-10">
      <Link to="/download">
        <Plus aria-hidden />
        New download
      </Link>
    </Button>
  );
}

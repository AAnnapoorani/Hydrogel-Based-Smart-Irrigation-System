"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import PlantsPage from "@/app/plants/page";

export default function RecommenderRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    // Soft redirect so URL becomes /plants?tab=recommender
    router.replace("/plants?tab=recommender");
  }, [router]);

  return <PlantsPage />;
}

import { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AppShell } from "@/components/AppShell";
import Dashboard from "@/pages/Dashboard";
import SourceIndex from "@/pages/SourceIndex";
import Contradictions from "@/pages/Contradictions";
import Priority from "@/pages/Priority";
import Artifacts from "@/pages/Artifacts";
import Report from "@/pages/Report";

function App() {
  useEffect(() => {
    document.documentElement.classList.add("dark");
  }, []);

  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/sources" element={<SourceIndex />} />
          <Route path="/contradictions" element={<Contradictions />} />
          <Route path="/priority" element={<Priority />} />
          <Route path="/artifacts" element={<Artifacts />} />
          <Route path="/report" element={<Report />} />
        </Routes>
      </AppShell>
      <Toaster position="bottom-right" richColors />
    </BrowserRouter>
  );
}

export default App;

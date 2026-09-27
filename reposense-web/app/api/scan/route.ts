import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const EXTENSION_MAP: Record<string, string> = {
  ".py": "Python",
  ".js": "JavaScript",
  ".ts": "TypeScript",
  ".tsx": "TypeScript",
  ".jsx": "JavaScript",
  ".md": "Markdown",
  ".json": "JSON",
  ".html": "HTML",
  ".css": "CSS",
};

const ONBOARDING_FILES = [
  "README", "README.md", "pyproject.toml", "setup.py", "setup.cfg",
  "LICENCE", "LICENSE", ".gitignore", "requirements.txt", "Pipfile",
  "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
  ".env.example", "CONTRIBUTING", "CONTRIBUTING.md", "CHANGELOG",
  "CHANGELOG.md", "CI config"
];

function analyzeFolder(dirPath: string) {
  let totalFiles = 0;
  let totalLines = 0;
  const langCount: Record<string, { files: number; lines: number }> = {};
  const presentFiles: string[] = [];
  const findings: any[] = [];

  function scanDir(current: string) {
    const entries = fs.readdirSync(current, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.name.startsWith(".") && entry.name !== ".gitignore") continue;
      if (["node_modules", "venv", ".venv", "__pycache__"].includes(entry.name)) continue;

      const fullPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        scanDir(fullPath);
      } else if (entry.isFile()) {
        totalFiles++;
        const ext = path.extname(entry.name).toLowerCase();
        const lang = EXTENSION_MAP[ext] || "Other";

        let lines = 0;
        try {
          const content = fs.readFileSync(fullPath, "utf-8");
          const splitLines = content.split("\n");
          lines = splitLines.length;

          splitLines.forEach((lineText, idx) => {
            if (/api_key\s*=\s*['"][^'"]+['"]/i.test(lineText)) {
              findings.push({
                file: fullPath,
                line: idx + 1,
                category: "Security",
                label: "Hardcoded secret (assignment)",
                snippet: lineText.trim(),
              });
            }
            if (/print\(.*\)/.test(lineText)) {
              findings.push({
                file: fullPath,
                line: idx + 1,
                category: "Code Smell",
                label: "print() statement (debug artifact)",
                snippet: lineText.trim(),
              });
            }
          });
        } catch {}

        totalLines += lines;
        if (!langCount[lang]) langCount[lang] = { files: 0, lines: 0 };
        langCount[lang].files += 1;
        langCount[lang].lines += lines;

        if (ONBOARDING_FILES.includes(entry.name)) {
          if (!presentFiles.includes(entry.name)) presentFiles.push(entry.name);
        }
      }
    }
  }

  scanDir(dirPath);

  const missing = ONBOARDING_FILES.filter((f) => !presentFiles.includes(f));
  const language_summary = Object.keys(langCount).map((l) => ({
    language: l,
    file_count: langCount[l].files,
    total_lines: langCount[l].lines,
  }));

  return {
    totals: { total_files: totalFiles, total_lines: totalLines },
    language_summary,
    onboarding: { present: presentFiles, missing },
    security_stats: {
      total_findings: findings.length,
      high: findings.filter((f) => f.category === "Security").length,
      medium: 0,
      low: findings.filter((f) => f.category === "Code Smell").length,
      info: 0,
    },
    security_findings: findings,
  };
}

export async function POST(req: Request) {
  try {
    const { repo_path } = await req.json();
    if (!repo_path || !fs.existsSync(repo_path)) {
      return NextResponse.json({ detail: "Directory path not found" }, { status: 400 });
    }
    const data = analyzeFolder(repo_path);
    return NextResponse.json({ status: "success", data });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message }, { status: 500 });
  }
}

import pathlib
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

async def run_agent(server_params: StdioServerParameters, resume_path: str, job_posts_path: str, target_jobs_path: str) -> None:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as client:
            await client.initialize()
            # 1. Load résumé PDF
            pdf_res = await client.call(
                "fetch_pdf_as_text",
                {"path": resume_path[:-4] + ".pdf"}
            )
            resume_text = pdf_res["text"]

            # 2. Load job posts CSV
            jobs_res = await client.call(
                "load_job_posts",
                {"csv_path": job_posts_path}
            )
            jobs = jobs_res["jobs"][:3]          # take first 3 for demo

            # 3. Compare each job description to résumé
            scores = []
            for job in jobs:
                result = await client.call(
                    "compare_resume_job",
                    {
                        "resume_text": resume_text,
                        "job_desc":    job["description"],
                        "company":     job["company"],
                        "title":       job["title"],
                    },
                )
                scores.append(result)

            # 4. Rank / filter
            ranked = await client.call(
                "rank_and_filter_jobs",
                {
                    "jobs":   jobs,
                    "scores": scores,
                    "max_per_company": 2,
                },
            )
            top_jobs = ranked["filtered_jobs"]

            # 5. Tailor resume for the top job
            if top_jobs:
                best = top_jobs[0]
                tex_res = await client.call(
                    "tailor_resume_tex",
                    {
                        "original_tex": pathlib.Path(resume_path).read_text(),
                        "job_desc":  best["description"],
                        "company":   best["company"],
                        "title":     best["title"],
                        "job_id":    best["job_id"],
                    },
                )
                print("Tailored résumé saved →", tex_res["path"])

            # 6. Persist results
            await client.call(
                "save_target_jobs",
                {
                    "jobs":       top_jobs,
                    "output_path": target_jobs_path,
                },
            )

if __name__ == "__main__":
    # This part is for standalone testing of the agent runner
    # You would typically run it from main.py
    pass

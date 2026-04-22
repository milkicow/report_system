"""
Seed data: three teams — AAA, Compilers, ParaCL.
  - 1 tech lead across all three groups (tech_lead role)
  - 1 devops user shared across all projects
  - Each team has its own team lead + 2-3 developers
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from datetime import date, datetime, timedelta, timezone
from app.auth import hash_password
from app.database import SessionLocal, engine, Base
from app.models import User, Team, TeamMember, Project, ProjectMember, Report, Issue

_pw = hash_password("dev123!")

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
db = SessionLocal()
now = datetime.now(timezone.utc)

# ─── Users ───────────────────────────────────────────────────────────────────
print("Creating users...")

tech_lead = User(
    name="Igor Smirnov", email="igor@corp.io", role="manager", password_hash=_pw
)
devops = User(
    name="Artem Devops", email="artem@corp.io", role="devops", password_hash=_pw
)

# AAA team
lead_aaa = User(
    name="MaXxx67", email="maxxx67@corp.io", role="developer", password_hash=_pw
)
dev_aaa1 = User(
    name="Bombardiro Crocodilo",
    email="bombardiro@corp.io",
    role="developer",
    password_hash=_pw,
)
dev_aaa2 = User(
    name="Brr Brr Patapim", email="brrbrr@corp.io", role="developer", password_hash=_pw
)
tester_aaa = User(
    name="Lirili Larila", email="lirili@corp.io", role="tester", password_hash=_pw
)

# Compilers team
lead_com = User(
    name="Aleksander Plastinin",
    email="plastinin@corp.io",
    role="developer",
    password_hash=_pw,
)
dev_com1 = User(
    name="Chimpanzini Bananini",
    email="chimpanzini@corp.io",
    role="developer",
    password_hash=_pw,
)
dev_com2 = User(
    name="Frulli Frulla", email="frulli@corp.io", role="developer", password_hash=_pw
)

# ParaCL team
lead_par = User(
    name="Tung Tung Tung Sahur",
    email="tung@corp.io",
    role="developer",
    password_hash=_pw,
)
dev_par1 = User(
    name="Tralalero Tralala",
    email="tralalero@corp.io",
    role="developer",
    password_hash=_pw,
)
dev_par2 = User(
    name="Ballerina Cappuchino",
    email="ballerina@corp.io",
    role="developer",
    password_hash=_pw,
)
dev_par3 = User(
    name="Alexandr Dolgov", email="dolgov@corp.io", role="developer", password_hash=_pw
)

all_users = [
    tech_lead,
    devops,
    lead_aaa,
    dev_aaa1,
    dev_aaa2,
    tester_aaa,
    lead_com,
    dev_com1,
    dev_com2,
    lead_par,
    dev_par1,
    dev_par2,
    dev_par3,
]
for u in all_users:
    db.add(u)
db.commit()
for u in all_users:
    db.refresh(u)
print(f"  {len(all_users)} users")

# ─── Teams ───────────────────────────────────────────────────────────────────
print("Creating teams...")

team_aaa = Team(
    name="AAA",
    description="High-load authorization server development team",
    lead_id=lead_aaa.id,
)
team_com = Team(
    name="Compilers",
    description="Compiler technologies team: parser, optimizer, code generator",
    lead_id=lead_com.id,
)
team_par = Team(
    name="ParaCL",
    description="Parallel CL language interpreter with GPU dev",
    lead_id=lead_par.id,
)

for t in [team_aaa, team_com, team_par]:
    db.add(t)
db.commit()
for t in [team_aaa, team_com, team_par]:
    db.refresh(t)
print("  3 teams: AAA, Compilers, ParaCL")

# ─── Team Members ────────────────────────────────────────────────────────────
print("Adding team members...")

team_members = [
    TeamMember(team_id=team_aaa.id, user_id=tech_lead.id),
    TeamMember(team_id=team_aaa.id, user_id=devops.id),
    # AAA
    TeamMember(team_id=team_aaa.id, user_id=lead_aaa.id),
    TeamMember(team_id=team_aaa.id, user_id=dev_aaa1.id),
    TeamMember(team_id=team_aaa.id, user_id=dev_aaa2.id),
    TeamMember(team_id=team_aaa.id, user_id=tester_aaa.id),
    # Compilers
    TeamMember(team_id=team_com.id, user_id=tech_lead.id),
    TeamMember(team_id=team_com.id, user_id=devops.id),
    TeamMember(team_id=team_com.id, user_id=lead_com.id),
    TeamMember(team_id=team_com.id, user_id=dev_com1.id),
    TeamMember(team_id=team_com.id, user_id=dev_com2.id),
    # ParaCL
    TeamMember(team_id=team_par.id, user_id=tech_lead.id),
    TeamMember(team_id=team_par.id, user_id=devops.id),
    TeamMember(team_id=team_par.id, user_id=lead_par.id),
    TeamMember(team_id=team_par.id, user_id=dev_par1.id),
    TeamMember(team_id=team_par.id, user_id=dev_par2.id),
    TeamMember(team_id=team_par.id, user_id=dev_par3.id),
]
for m in team_members:
    db.add(m)
db.commit()
print(f"  {len(team_members)} team memberships")

# ─── Projects ────────────────────────────────────────────────────────────────
print("Creating projects...")

proj_aaa = Project(
    name="AAA",
    description="Triple A team",
    team_id=team_aaa.id,
    deadline=now + timedelta(days=45),
    budget_hours=400.0,
    status="active",
)
proj_com = Project(
    name="Compilers Toolchain",
    description="LLVM-based compiler with some post-link optimizations",
    team_id=team_com.id,
    deadline=now + timedelta(days=60),
    budget_hours=600.0,
    status="active",
)
proj_par = Project(
    name="ParaCL Interpreter",
    description="ParaCl language design and toolchain",
    team_id=team_par.id,
    deadline=now + timedelta(days=30),
    budget_hours=350.0,
    status="active",
)

for p in [proj_aaa, proj_com, proj_par]:
    db.add(p)
db.commit()
for p in [proj_aaa, proj_com, proj_par]:
    db.refresh(p)
print("  3 projects")

# ─── Project Members ─────────────────────────────────────────────────────────
proj_members = [
    # AAA project
    ProjectMember(
        project_id=proj_aaa.id, user_id=tech_lead.id, member_role="tech_lead"
    ),
    ProjectMember(project_id=proj_aaa.id, user_id=devops.id, member_role="devops"),
    ProjectMember(project_id=proj_aaa.id, user_id=lead_aaa.id, member_role="team_lead"),
    ProjectMember(project_id=proj_aaa.id, user_id=dev_aaa1.id, member_role="developer"),
    ProjectMember(project_id=proj_aaa.id, user_id=dev_aaa2.id, member_role="developer"),
    ProjectMember(project_id=proj_aaa.id, user_id=tester_aaa.id, member_role="tester"),
    # Compilers project
    ProjectMember(
        project_id=proj_com.id, user_id=tech_lead.id, member_role="tech_lead"
    ),
    ProjectMember(project_id=proj_com.id, user_id=devops.id, member_role="devops"),
    ProjectMember(project_id=proj_com.id, user_id=lead_com.id, member_role="team_lead"),
    ProjectMember(project_id=proj_com.id, user_id=dev_com1.id, member_role="developer"),
    ProjectMember(project_id=proj_com.id, user_id=dev_com2.id, member_role="developer"),
    # ParaCL project
    ProjectMember(
        project_id=proj_par.id, user_id=tech_lead.id, member_role="tech_lead"
    ),
    ProjectMember(project_id=proj_par.id, user_id=devops.id, member_role="devops"),
    ProjectMember(project_id=proj_par.id, user_id=lead_par.id, member_role="team_lead"),
    ProjectMember(project_id=proj_par.id, user_id=dev_par1.id, member_role="developer"),
    ProjectMember(project_id=proj_par.id, user_id=dev_par2.id, member_role="developer"),
    ProjectMember(project_id=proj_par.id, user_id=dev_par3.id, member_role="developer"),
]
for m in proj_members:
    db.add(m)
db.commit()

# ─── Issues ──────────────────────────────────────────────────────────────────
print("Creating issues...")


def make_issue(
    proj_id,
    assignee_id,
    title,
    status,
    itype,
    priority,
    pts,
    days_ago_closed=None,
    stale_days=None,
):
    closed_at = now - timedelta(days=days_ago_closed) if days_ago_closed else None
    updated_at = now - timedelta(days=stale_days) if stale_days else now
    return Issue(
        project_id=proj_id,
        assignee_id=assignee_id,
        title=title,
        status=status,
        issue_type=itype,
        priority=priority,
        story_points=pts,
        closed_at=closed_at,
        updated_at=updated_at,
    )


issues = [
    # AAA
    make_issue(
        proj_aaa.id,
        lead_aaa.id,
        "Design new generator",
        "closed",
        "task",
        "high",
        52,
        days_ago_closed=14,
    ),
    make_issue(
        proj_aaa.id,
        dev_aaa1.id,
        "Implement va2pa tool",
        "closed",
        "feature",
        "critical",
        8,
        days_ago_closed=7,
    ),
    make_issue(
        proj_aaa.id,
        dev_aaa2.id,
        "Deprecate legacy tools",
        "in_progress",
        "task",
        "high",
        5,
    ),
    make_issue(
        proj_aaa.id,
        dev_aaa1.id,
        "Bug: race condition in generator",
        "in_progress",
        "bug",
        "critical",
        3,
        stale_days=6,
    ),
    make_issue(
        proj_aaa.id,
        tester_aaa.id,
        "Test generation: 10k+",
        "open",
        "task",
        "high",
        5,
    ),
    make_issue(
        proj_aaa.id,
        dev_aaa2.id,
        "Test framework",
        "open",
        "feature",
        "medium",
        6,
    ),
    # Compilers
    make_issue(
        proj_com.id,
        lead_com.id,
        "Lexer: expression tokenization",
        "closed",
        "task",
        "high",
        5,
        days_ago_closed=10,
    ),
    make_issue(
        proj_com.id,
        dev_com1.id,
        "LL(1) parser — basic syntax",
        "closed",
        "feature",
        "critical",
        8,
        days_ago_closed=5,
    ),
    make_issue(
        proj_com.id,
        dev_com2.id,
        "AST: nodes for all expressions",
        "in_progress",
        "task",
        "high",
        5,
    ),
    make_issue(
        proj_com.id,
        dev_com1.id,
        "Semantic type analysis",
        "in_progress",
        "feature",
        "high",
        8,
        stale_days=7,
    ),
    make_issue(
        proj_com.id,
        dev_com2.id,
        "LLVM IR generation for basic types",
        "open",
        "feature",
        "critical",
        13,
    ),
    make_issue(
        proj_com.id,
        lead_com.id,
        "Bug: memory leak in AST on parse errors",
        "open",
        "bug",
        "high",
        3,
    ),
    # ParaCL
    make_issue(
        proj_par.id,
        lead_par.id,
        "ParaCL language specification v1.0",
        "closed",
        "task",
        "critical",
        3,
        days_ago_closed=12,
    ),
    make_issue(
        proj_par.id,
        dev_par1.id,
        "Interpreter: basic operations",
        "closed",
        "feature",
        "high",
        8,
        days_ago_closed=6,
    ),
    make_issue(
        proj_par.id,
        dev_par3.id,
        "Refactoring: add 67 constants and brainrot variable names",
        "open",
        "task",
        "critical",
        67,
    ),
    make_issue(
        proj_par.id,
        dev_par2.id,
        "Bug: deadlock in thread pool",
        "open",
        "bug",
        "critical",
        5,
    ),
    make_issue(proj_par.id, None, "Benchmarks vs NumPy", "open", "task", "medium", 3),
]
for i in issues:
    db.add(i)
db.commit()
print(f"  {len(issues)} issues")

# ─── Reports ─────────────────────────────────────────────────────────────────
print("Creating reports...")

reports = []
schedule = [
    # (user, project, hours/day, category, [rotating comments])
    (lead_aaa.id, proj_aaa.id, 6.0, "dev", [
        "Reviewed OAuth2 token refresh PR, left comments on error handling",
        "Architecture session: aligned JWT schema with the team",
        "Fixed race condition in token store — added mutex around write path",
        "Merged two PRs, updated task estimates for the sprint",
        "Investigated memory usage spike in prod-like environment",
    ]),
    (dev_aaa1.id, proj_aaa.id, 7.5, "dev", [
        "Implemented va2pa address translation tool",
        "Debugging race condition in session manager — root cause found",
        "OAuth2 flow: finished token issuance endpoint",
        "Writing unit tests for the token store",
        "Refactoring auth middleware based on review feedback",
    ]),
    (dev_aaa2.id, proj_aaa.id, 7.5, "dev", [
        "Working on refresh token rotation logic",
        "Redis cache integration: spike complete, straightforward path forward",
        "Deprecating legacy auth endpoints — cleanup in progress",
        "Added expiry handling for refresh tokens",
        "Pair programming with Bombardiro on session concurrency fix",
    ]),
    (tester_aaa.id, proj_aaa.id, 5.0, "review", [
        "Reviewed auth flow test cases, found 2 edge cases in token expiry",
        "Set up load testing environment with k6",
        "5k rps load test passed, documented results",
        "Writing test plan for 10k rps run",
        "Reviewed token rotation PR, approved with minor notes",
    ]),
    (devops.id, proj_aaa.id, 3.0, "devops", [
        "CI pipeline for AAA: added lint and test stages",
        "Configured staging environment for AAA services",
        "Secrets rotation in Vault for AAA",
        "Fixed flaky test step in AAA pipeline",
        "Updated deploy scripts for zero-downtime rolling restart",
    ]),
    (devops.id, proj_com.id, 2.5, "devops", [
        "CI pipeline for Compilers toolchain: build and unit test stages",
        "Docker image optimization — reduced build time by 40%",
        "Configured artifact upload for compiler binaries",
        "Added cache for LLVM build dependencies",
        "Fixed linker path issue in CI Docker image",
    ]),
    (devops.id, proj_par.id, 2.5, "devops", [
        "CI for ParaCL: added CUDA/OpenCL driver install step",
        "Fixed OpenCL driver compatibility on CI runner",
        "Configured mock device mode for CI environments without GPU",
        "Set up nightly benchmark job for ParaCL",
        "Dockerized ParaCL build — works on CPU-only runners now",
    ]),
    (lead_com.id, proj_com.id, 6.0, "dev", [
        "Lexer complete and merged to main",
        "Reviewing LL(1) parser PR — two shift/reduce conflicts to resolve",
        "Drafted design doc for semantic analysis pass structure",
        "Code review session with the team, discussed AST visitor pattern",
        "Triaged memory leak bug — narrowed to AST cleanup on parse errors",
    ]),
    (dev_com1.id, proj_com.id, 8.0, "dev", [
        "LL(1) parser: basic syntax parsing complete",
        "Opened PR for parser, addressing shift/reduce review comments",
        "Started semantic type analysis module",
        "Added error recovery to parser — continues past bad tokens",
        "Tests for LL(1) parser: 30 cases, all passing",
    ]),
    (dev_com2.id, proj_com.id, 8.0, "dev", [
        "AST: designed node hierarchy for all expression types",
        "Implementing statement nodes — if/while/block",
        "Blocked on parser interface — reading Chimpanzini's PR to align",
        "AST pretty-printer for debug output",
        "Visitor pattern scaffolding for AST traversal passes",
    ]),
    (lead_par.id, proj_par.id, 6.0, "dev", [
        "Language spec v1.0 finalized and published in the repo",
        "Unblocked interpreter track with spec clarifications on scoping rules",
        "Reviewed interpreter PR, left detailed comments on error handling",
        "Team sync: aligned on OpenCL backend interface contract",
        "Updated spec: added parallel map/reduce semantics section",
    ]),
    (dev_par1.id, proj_par.id, 7.5, "dev", [
        "Interpreter: arithmetic and variable ops working end-to-end",
        "Implemented control flow — if/else, while loop",
        "Parallel map/reduce: blocked on OpenCL backend init from Ballerina",
        "Basic function call support in interpreter",
        "Error messages for type mismatches — user-friendly output",
    ]),
    (dev_par2.id, proj_par.id, 7.5, "dev", [
        "OpenCL context initialization working on dev machine",
        "Device enumeration: correctly detects GPU and CPU devices",
        "Driver compatibility issue on CI runner — investigating workaround",
        "Mock device mode implemented for CPU-only CI",
        "Buffer allocation and kernel enqueue prototype working",
    ]),
    (dev_par3.id, proj_par.id, 5.0, "review", [
        "Reviewed interpreter PR: approved with minor style comments",
        "Code review for OpenCL backend — buffer lifetime looks correct",
        "Reviewed spec update for map/reduce — left questions on reduction order",
        "Reviewed test suite PR, suggested additional edge cases",
        "Approved parallel map/reduce PR after second round of review",
    ]),
    (dev_par3.id, proj_par.id, 67.0, "dev", [
        "Added 67 constants with brainrot variable names to ParaCL stdlib",
        "Refactoring: renamed everything to brainrot convention as requested",
        "Added bombardiro_crocodilo() builtin — critical for spec compliance",
        "Documented all 67 constants in the spec appendix",
        "Fixed import order for brainrot constants module",
    ]),
    (tech_lead.id, proj_aaa.id, 1.5, "meeting", [
        "Weekly sync with AAA team — on track, no blockers",
        "Reviewed AAA progress: escalated race condition as high risk",
        "Sprint planning for AAA: re-estimated token rotation story",
        "Checked in on load test results, approved 10k rps target",
        "Retrospective with AAA — process improvements identified",
    ]),
    (tech_lead.id, proj_com.id, 1.5, "meeting", [
        "Compilers sync — parser slightly behind, monitoring closely",
        "Discussed LLVM IR gen scope and timeline with Plastinin",
        "Sprint planning for Compilers team",
        "Reviewed memory leak triage, prioritized as high",
        "Retrospective with Compilers team — AST rework added buffer week",
    ]),
    (tech_lead.id, proj_par.id, 1.5, "meeting", [
        "ParaCL sync — OpenCL driver issue escalated to infra team",
        "Gave sign-off on language spec v1.0",
        "Sprint planning for ParaCL — adjusted scope after driver delay",
        "Checked in on mock device workaround, approved for CI unblock",
        "Retrospective with ParaCL — driver issue resolved, back on track",
    ]),
]

for days_ago in range(1, 15):
    report_date = date.today() - timedelta(days=days_ago)
    if report_date.weekday() >= 5:
        continue  # skip weekends
    for user_id, proj_id, hours, cat, comments in schedule:
        reports.append(
            Report(
                user_id=user_id,
                project_id=proj_id,
                report_date=report_date,
                hours_spent=hours,
                category=cat,
                comment=comments[days_ago % len(comments)],
            )
        )

for r in reports:
    db.add(r)
db.commit()
print(f"  {len(reports)} reports")

db.close()
print("\nDone! Run: uvicorn app.main:app --reload")
print("   Docs: http://127.0.0.1:8000/docs")

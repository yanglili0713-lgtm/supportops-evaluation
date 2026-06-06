// IncidentOps GraphRAG Neo4j-style schema.
// This file is documentation and an optional production starting point.
// Tests use graph/build_graph.py with data/graph_seed.json instead of Neo4j.

CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE;
CREATE CONSTRAINT team_id IF NOT EXISTS FOR (t:Team) REQUIRE t.team_id IS UNIQUE;
CREATE CONSTRAINT project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.project_id IS UNIQUE;
CREATE CONSTRAINT upload_job_id IF NOT EXISTS FOR (j:UploadJob) REQUIRE j.upload_job_id IS UNIQUE;
CREATE CONSTRAINT error_code IF NOT EXISTS FOR (e:ErrorCode) REQUIRE e.error_code IS UNIQUE;
CREATE CONSTRAINT service_id IF NOT EXISTS FOR (s:Service) REQUIRE s.service_id IS UNIQUE;
CREATE CONSTRAINT ticket_id IF NOT EXISTS FOR (t:Ticket) REQUIRE t.ticket_id IS UNIQUE;
CREATE CONSTRAINT skill_name IF NOT EXISTS FOR (s:Skill) REQUIRE s.skill_name IS UNIQUE;

MERGE (u:User {user_id: "u_1001", email: "alice@example.com"})
MERGE (team:Team {team_id: "team_01", name: "Search Platform"})
MERGE (project:Project {project_id: "proj_rag_01", name: "Knowledge Upload"})
MERGE (job:UploadJob {upload_job_id: "upload_7001", file_type: "PDF", status: "failed"})
MERGE (err:ErrorCode {error_code: "EMBEDDING_FAILED"})
MERGE (svc:Service {service_id: "embedding_service", name: "Embedding Service"})
MERGE (ticket:Ticket {ticket_id: "ticket_3001", summary: "PDF upload failed during embedding"})
MERGE (skill:Skill {skill_name: "rag_upload_debug"})
MERGE (step:SOPStep {step_id: "check_ocr", description: "Check OCR and embedding job status"})
MERGE (u)-[:MEMBER_OF]->(team)
MERGE (team)-[:OWNS]->(project)
MERGE (project)-[:HAS_UPLOAD]->(job)
MERGE (job)-[:FAILED_WITH]->(err)
MERGE (err)-[:RAISED_BY]->(svc)
MERGE (ticket)-[:MENTIONS]->(err)
MERGE (ticket)-[:RELATED_TO]->(project)
MERGE (skill)-[:HANDLES]->(err)
MERGE (skill)-[:REQUIRES_STEP]->(step);

// Example queries:
// MATCH (u:User {user_id: $user_id})-[:MEMBER_OF]->(:Team)-[:OWNS]->(p:Project)-[:HAS_UPLOAD]->(j:UploadJob) RETURN p, j;
// MATCH (e:ErrorCode {error_code: $error_code})<-[:MENTIONS]-(t:Ticket), (e)-[:RAISED_BY]->(s:Service) RETURN e, s, t;
// MATCH (s:Service {service_id: $service_id})-[:DEPENDS_ON]->(dep:Service) RETURN s, dep;

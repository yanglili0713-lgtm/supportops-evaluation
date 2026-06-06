from __future__ import annotations


class Neo4jAdapter:
    """Optional adapter placeholder.

    Production can wire a real Neo4j driver here. The default project path uses
    in-memory graph data so tests never require a running Neo4j service.
    """

    USER_CONTEXT_QUERY = """
    MATCH (u:User {user_id: $user_id})-[:MEMBER_OF]->(:Team)-[:OWNS]->(p:Project)-[:HAS_UPLOAD]->(j:UploadJob)
    RETURN p, j
    """

    ERROR_CONTEXT_QUERY = """
    MATCH (e:ErrorCode {error_code: $error_code})
    OPTIONAL MATCH (e)-[:RAISED_BY]->(s:Service)
    OPTIONAL MATCH (t:Ticket)-[:MENTIONS]->(e)
    OPTIONAL MATCH (skill:Skill)-[:HANDLES]->(e)
    RETURN e, s, t, skill
    """

    SERVICE_DEPENDENCY_QUERY = """
    MATCH (s:Service {service_id: $service_id})-[:DEPENDS_ON]->(dep:Service)
    RETURN s, dep
    """

    def __init__(self, driver=None) -> None:
        self.driver = driver

    def is_configured(self) -> bool:
        return self.driver is not None

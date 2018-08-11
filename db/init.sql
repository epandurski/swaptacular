CREATE FUNCTION create_user_with_own_schema(username text, password text DEFAULT NULL) RETURNS void
AS $$
BEGIN
  EXECUTE format('CREATE USER %I WITH PASSWORD %L', username, COALESCE(password, username));
  EXECUTE format('CREATE SCHEMA AUTHORIZATION %I', username);
END;
$$ LANGUAGE plpgsql;


SELECT create_user_with_own_schema('users_service');

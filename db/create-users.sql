CREATE OR REPLACE FUNCTION create_user_with_own_schema(username text, password text DEFAULT NULL) RETURNS void
AS $$
BEGIN
  EXECUTE format('CREATE USER %I WITH PASSWORD %L', username, COALESCE(password, username));
  EXECUTE format('CREATE SCHEMA AUTHORIZATION %I', username);
  RAISE NOTICE 'created role "%"', username;
EXCEPTION
  WHEN duplicate_object THEN
    RAISE NOTICE 'role "%" already exists ', username;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION create_users_with_own_schemas() RETURNS text
AS $$
BEGIN
  --------------------------
  -- Add your users here! --
  --------------------------
  PERFORM create_user_with_own_schema('users_service');
  PERFORM create_user_with_own_schema('hydra_service');
  PERFORM create_user_with_own_schema('oathkeeper_service');
  RETURN 'ok';
END;
$$ LANGUAGE plpgsql;


SELECT create_users_with_own_schemas();

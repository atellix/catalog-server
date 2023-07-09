-- Find or create entry_type row
DELIMITER //
CREATE FUNCTION entry_type_id(typeName VARCHAR(128)) RETURNS BIGINT
BEGIN
  DECLARE typeId BIGINT;
  -- Attempt to find the entry type by type_name
  SELECT id INTO typeId FROM entry_type WHERE type_name = typeName LIMIT 1;
  -- If the entry type doesn't exist, create a new record
  IF typeId IS NULL THEN
    INSERT INTO entry_type (type_name) VALUES (typeName);
    SET typeId = LAST_INSERT_ID();
  END IF;
  RETURN typeId;
END //
DELIMITER ;

-- Get uri hash (if exists)
DELIMITER //
CREATE FUNCTION get_uri_hash(uriText VARCHAR(128)) RETURNS BINARY(16)
DETERMINISTIC
BEGIN
  DECLARE uriHash BINARY(16);
  SELECT uri_hash INTO uriHash FROM uri WHERE uri = uriText LIMIT 1;
  RETURN uriHash;
END //
DELIMITER ;


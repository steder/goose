CREATE  TABLE IF NOT EXISTS goosetest.Track (
  TrackId INT NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (TrackId) )
ENGINE = InnoDB;

-- Just to confirm that multiple sql statements work:

SELECT * FROM Track;
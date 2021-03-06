CREATE TABLE "SPIDER  "."NEWS"  (
		  "ID" INTEGER NOT NULL GENERATED ALWAYS AS IDENTITY (  
		    START WITH +1  
		    INCREMENT BY +1  
		    MINVALUE +1  
		    MAXVALUE +2147483647  
		    NO CYCLE  
		    CACHE 20  
		    NO ORDER ) , 
		  "URL" VARCHAR(255 OCTETS) NOT NULL , 
		  "BATCH" VARCHAR(255 OCTETS) , 
		  "CONTENT" CLOB(1048576 OCTETS) LOGGED NOT COMPACT , 
		  "COVER" BLOB(2147483647) LOGGED NOT COMPACT , 
		  "PDF" BLOB(2147483647) LOGGED NOT COMPACT , 
		  "HOT" VARCHAR(255 OCTETS) , 
		  "KEYWORDS" VARCHAR(255 OCTETS) , 
		  "TITLE" VARCHAR(255 OCTETS) , 
		  "TYPE" VARCHAR(255 OCTETS) , 
		  "UPDATE" VARCHAR(255 OCTETS) )   
		 IN "USERSPACE1"  
		 ORGANIZE BY ROW; 
ALTER TABLE "SPIDER  "."NEWS" ALTER COLUMN "ID" RESTART WITH 1

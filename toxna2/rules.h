#ifndef RULES_H_INCLUDED
#define RULES_H_INCLUDED

#include "misc.h"

#define RULE_STATUS_EXHAUSTED  (-2)
#define RULE_STATUS_ERROR      (-1)
#define RULE_STATUS_OK         (0)


/* the different kinds of rule terms */
typedef enum
{
	TERM_DIGIT, TERM_LATIN, TERM_ASCII, TERM_LEXICON
} term_type_t;

/* representes a rule term */
typedef struct
{
	term_type_t type;              /* term's type (e.g., '@' in "@7") */
	int count;                     /* term's count (e.g., 7 in "@7") */

	int k;                         /* the index of the next k to use when flag=ALL */
	int limit;                     /* total number of values generated by this term */
	int max_size;                  /* max size in bytes of the output that may be generated
								      by this term*/
} term_info_t;

/* representes a complete rule */
typedef struct
{
	int num_of_terms;               /* number of rule terms */
	term_info_t * terms;            /* array of terms (dynamically allocated) */

	int num_of_words;               /* number of words in lexicon */
	int longest_word;               /* longest word in the lexicon */
	char ** words;                  /* lexicon (dynamically allocated) */

	BasicHashFunctionPtr hashfunc;  /* the hash function (function pointer) */
	char hashname[10];              /* '10' is taken from deht.h */

	int limit;                      /* the "flag"; -1 means "all" */
	int remaining;                  /* the number of remaining passwords, when flag='n' */
} rule_info_t;

/* 
 * APIs (documented in the C file) 
 */
int rule_load_from_file(rule_info_t * info, const char * inifilename);
int rule_init(rule_info_t * info, const char * pattern,
        const char * lexfilename, const char * hashname, const char * flag);
void rule_finalize(rule_info_t * info);

unsigned long rule_num_of_passwords(rule_info_t * info);
int rule_max_password_length(rule_info_t * info);
int rule_generate_next_password(rule_info_t * info, char * output, int output_length);


#endif /* RULES_H_INCLUDED */

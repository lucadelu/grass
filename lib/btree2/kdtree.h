/*!
 * \file kdtree.c
 *
 * \brief binary search tree 
 *
 * Dynamic balanced k-d tree implementation
 *
 * (C) 2014 by the GRASS Development Team
 *
 * This program is free software under the GNU General Public License
 * (>=v2).  Read the file COPYING that comes with GRASS for details.
 *
 * \author Markus Metz
 */

/***********************************************************************
 * k-d tree: 
 * multidimensional binary search tree for nearest neighbor search
 * 
 * Bentley, J. L. (1975). "Multidimensional binary search trees used for 
 * associative searching". Communications of the ACM 18 (9): 509.
 * doi:10.1145/361002.361007
 * 
 * This k-d tree is a dynamic tree:
 * elements can be inserted and removed any time
 * 
 * this k-d tree is balanced:
 * subtrees have a similar depth (the difference in subtrees' depths is 
 * not allowed to be larger than the balancing tolerance)
 * 
 * USAGE:
 * create a new k-d tree
 * kdtree_create();
 * 
 * insert points into the tree
 * kdtree_insert();
 * 
 * optionally optimize the tree:
 * kdtre_optimize
 * 
 * search k nearest neighbours
 * kdtree_knn();
 * 
 * search all neighbors in radius
 * kdtree_dnn();
 * 
 * destroy the tree:
 * kdtree_destroy();
 * 
 ***********************************************************************/

struct kdnode
{
    unsigned char dim;		/* split dimension of this node */
    unsigned char depth;	/* depth at this node */
    double *c;			/* coordinates */
    int uid;			/* unique id of this node */
    struct kdnode *child[2];	/* link to children: link[0] for smaller, link[1] for larger */
};

struct kdtree
{
    unsigned char ndims;	/* number of dimensions */
    unsigned char *nextdim;	/* split dimension of child nodes */
    int csize;			/* size of coordinates in bytes */
    int btol;			/* balancing tolerance */
    size_t count;		/* number of items in the tree */
    struct kdnode *root;	/* tree root */
};

/* creae a new k-d tree */
struct kdtree *kdtree_create(char ndims,	/* number of dimensions */
                             int *btol);	/* optional balancing tolerance */

/* destroy a tree */
void kdtree_destroy(struct kdtree *t);

/* clear a tree, removing all entries */
void kdtree_clear(struct kdtree *t);

/* insert an item (coordinates c and uid) into the k-d tree */
int kdtree_insert(struct kdtree *t,		/* k-d tree */
                  double *c,			/* coordinates */
		  int uid,			/* the point's unique id */
		  int dc);			/* allow duplicate coordinates */

/* remove an item from the k-d tree
 * coordinates c and uid must match */
int kdtree_remove(struct kdtree *t,		/* k-d tree */
                  double *c,			/* coordinates */
		  int uid);			/* the point's unique id */

/* find k nearest neighbors 
 * results are stored in uid (uids) and d (squared distances)
 * optionally an uid to be skipped can be given
 * useful when searching for the nearest neighbors of an item 
 * that is also in the tree */
int kdtree_knn(struct kdtree *t,		/* k-d tree */
               double *c,			/* coordinates */
	       int *uid,			/* unique ids of the neighbors */
	       double *d,			/* squared distances to the neighbors */
	       int k,				/* number of neighbors to find */
	       int *skip);			/* unique id to skip */


/* find all nearest neighbors within distance aka radius search
 * results are stored in puid (uids) and pd (squared distances)
 * memory is allocated as needed, the calling fn must free the memory
 * optionally an uid to be skipped can be given */
int kdtree_dnn(struct kdtree *t,		/* k-d tree */
               double *c,			/* coordinates */
	       int **puid,			/* unique ids of the neighbors */
	       double **pd,			/* squared distances to the neighbors */
	       double maxdist,			/* radius to search around the given coordinates */
	       int *skip);			/* unique id to skip */

/* k-d tree optimization, only useful if the tree will be heavily used
 * (more searches than items in the tree)
 * level 0 = a bit, 1 = more, 2 = a lot */
void kdtree_optimize(struct kdtree *t,		/* k-d tree */
                     int level);		/* optimization level */

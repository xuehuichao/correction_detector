#include <stdio.h>
#include <stdlib.h>
#include <Python.h>

static PyObject *AlignError;

static int all_are_integers(PyObject * array, int size) {
  int i;
  for (i = 0; i < size; ++i) {
    PyObject* item = PyList_GetItem(array, i);
    if (!PyInt_Check(item))
      return 0;
    long x = PyInt_AsLong(item);
    if (x < 0)
      return 0;
  }
  return 1;
}

static void copy_integers(PyObject * array, long * to_array) {
  int size = PyList_Size(array);
  int i;
  for (i = 0; i < size; ++i) {
    to_array[i] = PyInt_AsLong(PyList_GetItem(array, i));
  }
}

struct Choice {
  int cost;
  int prev_x;
  int prev_y;
  int cur_char_1;
  int cur_char_2;
};

static PyObject *
construct_editdistalign(int size1, long* array1,
                        int size2, long* array2) {
  struct Choice ** best_choices = (struct Choice **) malloc(
      sizeof(struct Choice *) * (size1 + 2));
  int i, j;
  for (i = 0; i <= size1; ++i)
    best_choices[i] = (struct Choice *) malloc(
        sizeof(struct Choice) * (size2 + 2));

  for (i = 1; i <= size1; ++i) {
    best_choices[i][0].cost = i;
    best_choices[i][0].prev_x = i-1;
    best_choices[i][0].prev_y = 0;
    best_choices[i][0].cur_char_1 = array1[i-1];
    best_choices[i][0].cur_char_2 = -1;
  }

  for (j = 1; j <= size2; ++j) {
    best_choices[0][j].cost = j;
    best_choices[0][j].prev_x = 0;
    best_choices[0][j].prev_y = j-1;
    best_choices[0][j].cur_char_1 = -1;
    best_choices[0][j].cur_char_2 = array2[j-1];
  }

  best_choices[0][0].cost = 0;
  best_choices[0][j].prev_x = -1;
  best_choices[0][j].prev_y = -1;
  best_choices[0][j].cur_char_1 = -1;
  best_choices[0][j].cur_char_2 = -1;

  for (i = 1; i <= size1; ++i) {
    for (j = 1; j <= size2; ++j) {
      struct Choice del_choice;
      del_choice.cost = best_choices[i-1][j].cost + 1;
      del_choice.prev_x = i-1;
      del_choice.prev_y = j;
      del_choice.cur_char_1 = array1[i-1];
      del_choice.cur_char_2 = -1;

      struct Choice ins_choice;
      ins_choice.cost = best_choices[i][j-1].cost + 1;
      ins_choice.prev_x = i;
      ins_choice.prev_y = j-1;
      ins_choice.cur_char_1 = -1;
      ins_choice.cur_char_2 = array2[j-1];

      struct Choice sub_choice;
      sub_choice.cost = best_choices[i-1][j-1].cost + ((array1[i-1] == array2[j-1])?0:1);
      sub_choice.prev_x = i-1;
      sub_choice.prev_y = j-1;
      sub_choice.cur_char_1 = array1[i-1];
      sub_choice.cur_char_2 = array2[j-1];

      struct Choice the_best = del_choice;
      if (the_best.cost > ins_choice.cost)
        the_best = ins_choice;
      if (the_best.cost > sub_choice.cost)
        the_best = sub_choice;

      best_choices[i][j] = the_best;
    }
  }

  PyObject* return_list = PyList_New(0);
  int cur_x = size1;
  int cur_y = size2;
  while (cur_x != 0 || cur_y != 0) {
    struct Choice * cur_best_choice = &best_choices[cur_x][cur_y];
    PyObject* choice_tuple = Py_BuildValue(
        "(ii)", cur_best_choice->cur_char_1, cur_best_choice->cur_char_2);
    PyList_Append(return_list, choice_tuple);
    Py_DECREF(choice_tuple);
    cur_x = cur_best_choice->prev_x;
    cur_y = cur_best_choice->prev_y;
  }
  PyList_Reverse(return_list);

  for (i = 0; i <= size1; ++i) {
    free(best_choices[i]);
  }
  free(best_choices);

  return return_list;
}

static PyObject *
editdistalign_align(PyObject *self, PyObject *args)
{
  PyObject * first_list;
  PyObject * second_list;
  
  if (!PyArg_ParseTuple(args, "OO", &first_list, &second_list)) {
    PyErr_SetString(AlignError, "Incorrect Argument");
    return NULL;
  }

  if (!PyList_Check(first_list) || !PyList_Check(second_list)) {
    PyErr_SetString(AlignError, "Incorrect argument type");
    return NULL;
  }

  int size_1 = PyList_Size(first_list);
  int size_2 = PyList_Size(second_list);

  if (!all_are_integers(first_list, size_1) || !all_are_integers(second_list, size_2)) {
    PyErr_SetString(AlignError, "Only accept non-negative integers as arguments");
    return NULL;
  }

  long * array1 = (long*)malloc(sizeof(long) * size_1);
  long * array2 = (long*)malloc(sizeof(long) * size_2);

  copy_integers(first_list, array1);
  copy_integers(second_list, array2);

  PyObject* result;
  result = construct_editdistalign(size_1, array1, size_2, array2);

  free(array1);
  free(array2);

  return result;
}

static PyMethodDef AlignMethods[] = {
    {"align",  editdistalign_align, METH_VARARGS,
     "Aligning two non-negative integer lists, and then provide an integer list containing tuples indicating which integer aligned to which."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
initeditdistalign(void)
{
    PyObject *m;

    m = Py_InitModule("editdistalign", AlignMethods);
    if (m == NULL)
        return;

    AlignError = PyErr_NewException("editdistalign.error", NULL, NULL);
    Py_INCREF(AlignError);
    PyModule_AddObject(m, "error", AlignError);
}


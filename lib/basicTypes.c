/*****************************************************************
* Basic Types implementation
******************************************************************/
#include "basicTypes.h"
#include <stdlib.h>
#include "str.h"
#include "stringUtil.h"
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>

int bt_size(bt_Type type) {   return type & 0x00ff;   }
bool bt_isInt(bt_Type type) { return !(type & 0xfe00); }
bool bt_isFloat(bt_Type type) { return type & 0x0200; }
bool bt_isnum(bt_Type type) { return !(type & 0xfc00); }
bool bt_isChar(bt_Type type) { return type & 0x0400; }
bool bt_isBool(bt_Type type) { return type & 0x0f00; }
bt_Type bt_setByteSize(short size) { return 0x04ff & size; } // 255 max

bool bt_convert_bool(String * str, bool * retBool) {
  if(cstr_eq_ignore_case(str->str, bt_TRUE) || atoi(str->str)) {
    *retBool = true;
} else if(cstr_eq_ignore_case(str->str, bt_FALSE) || str->str[0] == '0')
      *retBool = false;
  else
    return false;
  return true;
}

bool bt_convert_int(String * str, int * retInt) {
  char * ptr;
  *retInt = (int) strtol(str->str, &ptr, 0);
  return *ptr == '\0' && *(str->str) != '\0';
}

bool bt_convert_float(String * str, float * retFloat) {
  char * ptr;
  *retFloat = strtof(str->str, &ptr);
  return *ptr == '\0' && *(str->str) != '\0';
}

bool bt_convert_double(String * str, double * retDouble) {
  char * ptr;
  *retDouble = strtod(str->str, &ptr);
  return *ptr == '\0' && *(str->str) != '\0';
}


String * bt_toString(bt_Type type, void * data, char * precision) {
  String * str = malloc(sizeof(String));
  char fmtBuffer[10];
  int i = 0;
  fmtBuffer[i++] = '%';
  if(precision) {
   for(char * c = precision; *c; c++)
      fmtBuffer[i++] = *c;
   } else if(bt_isFloat(type)) {
      fmtBuffer[i++] = '.';
      fmtBuffer[i++] = '2';
   }
  switch(type) {
      case bt_UInt32:
        fmtBuffer[i++] = 'l';
        fmtBuffer[i++] = 'u';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, *((uint32_t *) data));
        break;
      case bt_Int32:
        fmtBuffer[i++] = 'd';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, *((int32_t *) data));
        break;
      case bt_UInt64:
        fmtBuffer[i++] = 'l';
        fmtBuffer[i++] = 'u';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, *((uint64_t *) data));
        break;
      case bt_Int64:
        fmtBuffer[i++] = 'l';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, *((int64_t *) data));
        break;
      case bt_UInt16:
        fmtBuffer[i++] = 'h';
        fmtBuffer[i++] = 'u';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, *((uint16_t *) data));
        break;
      case bt_Int16:
        fmtBuffer[i++] = 'h';
        fmtBuffer[i++] = 'i';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, *((int16_t *) data));
        break;
      case bt_Float32:
        fmtBuffer[i++] = 'f';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, *((float *) data));
        break;
      case bt_Double64:
        fmtBuffer[i++] = 'E';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, *((double *) data));
        break;
      case bt_UInt8:
        fmtBuffer[i++] = 'h';
        fmtBuffer[i++] = 'u';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, *((uint8_t *) data));
      break;
      case bt_Int8:
        fmtBuffer[i++] = 'h';
        fmtBuffer[i++] = 'i';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, *((int8_t *) data));
        break;
      case bt_Double128:
        fmtBuffer[i++] = 'E';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, *((long double *) data));
       break;
      case bt_Bool1:
        if(*((bool *) data)) {
          fmtBuffer[--i] = 'T';
          fmtBuffer[++i] = 'r';
          fmtBuffer[++i] = 'u';
        } else {
          fmtBuffer[--i] = 'F';
          fmtBuffer[++i] = 'a';
          fmtBuffer[++i] = 'l';
          fmtBuffer[++i] = 's';
        }
        fmtBuffer[++i] = 'e';
        fmtBuffer[++i] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, *((bool *) data));
        break;
      default:
        fmtBuffer[i++] = 'X'; // hex
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, (char *) data);
        break;
  }
  return str;
}
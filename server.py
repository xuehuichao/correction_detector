import corr_ext
import re

class AnnotatableSequence(object):
    def __init__(self, sequence):
        self.sequence = sequence
        self.annotations = []
        self.alarm = True

    def Annotate(self, range_start, range_end, tag):
        if range_start > range_end:
            if self.alarm:
                raise ValueError
            else:
                return
        for start, end, symbol in self.annotations:
            if start <= range_start < end or start < range_end < end:
                if self.alarm:
                    raise ValueError("Overlap in sequence: %r and %r" % (
                        (start, end), (range_start, range_end)))
                else:
                    return
        if range_start > len(self.sequence) or range_end < 0:
            if self.alarm:
                raise ValueError("The new annotation is out of range %r" % (
                    (range_start, range_end),))
            else:
                return
        self.annotations.append((range_start, range_end, tag))

    def GetSegments(self):
        self.annotations.sort()
        segments = []
        
        prev_end = 0
        for i in range(len(self.annotations)):
            start, end, tag = self.annotations[i]
            if start != prev_end:
                assert start > prev_end
                segments.append((self.sequence[prev_end:start], None))
            segments.append((self.sequence[start:end], tag))
            prev_end = end
        if prev_end < len(self.sequence):
            segments.append((self.sequence[prev_end:], None))
    
        return segments

    def SetOverlapAlarm(self, alarm_on):
        self.alarm = alarm_on

def GetErrorDesc(err_tp):
    error_types = {
        "F" : "wrong %s form",
        "M" : "%s missing",
        "R" : "%s needs replacing",
        "U" : "unnecessary %s",
        "D" : "%s wrongly derived",
        "C" : "%s countability",
        "FF" : "false %s friend",
        "AG" : "%s agreement",
        "AS" : "argument structure",
        "CE" : "compound error",
        "CL" : "collocation error",
        "ID" : "idiom error",
        "IN" : "incorrect noun plural",
        "IV" : "incorrect verb inflection",
        "L" : "inappropriate register",
        "S" : "spelling",
        "SA" : "American spelling",
        "SX" : "spelling confusion",
        "TV" : "wrong verb tense",
        "W" : "word order",
        "X" : "incorrect formation of negative",
        }

    word_classes = {
        "A" : "pronoun",
        "C" : "conjunction",
        "D" : "determiner",
        "J" : "adjective",
        "N" : "noun",
        "Q" : "quantifier",
        "T" : "preposition",
        "V" : "verb",
        "Y" : "adverb",
        "P" : "punctuation"
        }

    error_type_reg = "(%s)" % ("|".join(error_types))
    word_class_reg = "(%s)" % ("|".join(word_classes))

    mo = re.match('^%s%s$' % (error_type_reg, word_class_reg), err_tp)
    if mo is not None:
        if "%s" in error_types[mo.group(1)]:
            return error_types[mo.group(1)] % word_classes[mo.group(2)]
        else:
            return error_types[mo.group(1)]

    mo = re.match('^%s$' % error_type_reg, err_tp)
    if mo is not None:
        if "%s" in error_types[mo.group(1)]:
            return " ".join((error_types[mo.group(1)] % "").split())
        else:
            return error_types[mo.group(1)]
        
    
    return err_tp


def ExtractChunks(orig_words, revised_into_words):
    corrections = corr_ext.ExtractCorrections(orig_words, revised_into_words)

    ann_seq = AnnotatableSequence(orig_words)
    for tp, s, e, rev_into in corrections:
        ann_seq.Annotate(s, e, (rev_into, tp))
    segments = ann_seq.GetSegments()
    result = []
    for seg, annot in segments:
        
        if annot is None:
            rev_into, tp = None, None
        else:
            rev_into, tp = annot

        result.append([" ".join(seg), rev_into, tp and GetErrorDesc(tp) or None])
    return result

def Tokenize(rev_sent):
    suf = []
    if rev_sent.endswith('.'):
        suf.append('.')
        rev_sent = rev_sent[:-1]
    return rev_sent.split() + suf

def HandleWebRequest(orig_words, revised_sentence):
    revised_into_words = Tokenize(revised_sentence)
    return ExtractChunks(orig_words, revised_into_words)

def Testing():
    import pprint

    print GetErrorDesc('MV')
    print GetErrorDesc('UJ')
    print GetErrorDesc('X')
    print GetErrorDesc('BAD')
    
    pprint.pprint(HandleWebRequest(
        ["This", "sentense", "might", "have", "contain", "error", "."],
        "This sentence may have errors.",
        ))

def main():
    # Testing()
    pass

if __name__ == "__main__":
    main()

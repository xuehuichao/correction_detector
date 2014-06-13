"""
This scipt contains the function: ExtractCorrections(input_sentence_1, input_sentence_2)
Input: two lists of words
Output: list of tuples (error_type, start_ind, end_ind, corrected_into)
"""

import maxent
import nltk
from os import path
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
import editdistalign

model_path = '.'

selector_model_path = path.join(model_path, 'selector.model')
merger_model_path = path.join(model_path, 'merger.model')
eng_dict_word_list = path.join(model_path, 'wordsEn.txt')

wnl = WordNetLemmatizer()
all_pos = [wordnet.ADJ,
           wordnet.VERB,
           wordnet.NOUN,
           wordnet.ADV]

class EngWordList(object):
    def __init__(self, location):
        self.wordset = set()
        with open(location) as input_file:
            for line in input_file:
                self.wordset.add(line.strip())

    def HasWord(self, word):
        return word.lower() in self.wordset

    the_list = None
    @staticmethod
    def EngHasWord(word):
        if EngWordList.the_list is None:
            EngWordList.the_list = EngWordList(eng_dict_word_list)
        return EngWordList.the_list.HasWord(word)

def TagSentence(words):
     return [pos for (w, pos) in nltk.pos_tag(words)]

def _FetchIndexFromDict(w, dictionary):
    try:
        return dictionary[w]
    except KeyError:
        val = len(dictionary)
        dictionary[w] = val
        return val


def EditDistanceAlign(seq_a, seq_b):
    word_dict = dict()
    int_seq_a = []
    int_seq_b = []
    for w in seq_a:
        int_seq_a.append(_FetchIndexFromDict(w, word_dict))
    for w in seq_b:
        int_seq_b.append(_FetchIndexFromDict(w, word_dict))

    all_words = [None] * len(word_dict)
    for k, v in word_dict.iteritems():
        all_words[v] = k        
    align_result = editdistalign.align(int_seq_a, int_seq_b)
    result = []
    for (i, j) in align_result:
        if i == -1:
            i = None
        else:
            i = all_words[i]
        if j == -1:
            j = None
        else:
            j = all_words[j]
        result.append((i, j))
    return result

def CalculateEditDistance(seq1, seq2):
    aligned = EditDistanceAlign(seq1, seq2)
    return len([1 for x, y in aligned if x != y])


class Edit(object):
    def __init__(self, orig_words, rev_words, (o_s, o_e, r_s, r_e)):
        self.orig_words = orig_words
        self.rev_words = rev_words
        self.orig_pos = TagSentence(self.orig_words)
        self.rev_pos = TagSentence(self.rev_words)
        self.o_s, self.o_e, self.r_s, self.r_e = (o_s, o_e, r_s, r_e)

    def SentencesHaveIdenticalWordSets(self):
        return set(self.orig_words) == set(self.rev_words)

    def GetEditType(self):
        if self.o_s == self.o_e:
            return "INS"
        if self.r_s == self.r_e:
            return "DEL"
        return 'REP'

    def GetStartAt(self):
        return (self.o_s, self.r_s)

    def GetEndAt(self):
        return (self.o_e, self.r_e)

    def GetOrigPOS(self):
        return self.orig_pos[self.o_s:self.o_e]

    def GetRevPOS(self):
        return self.rev_pos[self.r_s:self.r_e]

    def GetOrigPhrase(self):
        return " ".join(self.orig_words[self.o_s:self.o_e])

    def GetRevPhrase(self):
        return " ".join(self.rev_words[self.r_s:self.r_e])




class EditDistancWithMergerBuilder(object):
    def __init__(self, merger, *args, **kw):
        self.merger = merger

    @staticmethod
    def ExtractBasicEdits(original, revision):
        aligned = EditDistanceAlign(original, revision)
        edits = []
        o_s = 0
        r_s = 0
        for x, y in aligned:
            if x is None:
                o_e = o_s
            else:
                o_e = o_s + 1

            if y is None:
                r_e = r_s
            else:
                r_e = r_s + 1

            if x != y:
                edits.append(
                    Edit(original, revision, (o_s, o_e, r_s, r_e)))
            o_s = o_e
            r_s = r_e
        assert o_e == len(original)
        assert r_e == len(revision)
        return edits

    def ExtractAnnotations(self, original, revision):
        edits = self.ExtractBasicEdits(original, revision)
        
        if len(edits) == 0:
            return []
        
        merging_inst_list = [MergingInst(edits, i)
                             for i in range(1, len(edits))]
        decisions = [self.merger.DecideMerge(inst) for inst in merging_inst_list]
        
        chunks = []
        cur_chunk = (0, 1)
        for i in range(1, len(edits)):
            if decisions[i-1]:
                cur_chunk = (cur_chunk[0], i + 1)
            else:
                chunks.append(cur_chunk)
                cur_chunk = (i, i + 1)
        chunks.append(cur_chunk)

        annotations = []
        for s, e in chunks:
            start_edit = edits[s]
            end_edit = edits[e - 1]
            o_s, r_s = start_edit.GetStartAt()
            o_e, r_e = end_edit.GetEndAt()
            annotations.append((o_s, o_e, " ".join(revision[r_s:r_e])))

        return annotations

class Merger(object):
    def __init__(self, classifier_location):
        self.classifier = maxent.MaxentModel()
        self.classifier.load(classifier_location)

    def DecideMerge(self, merging_inst): # NOT DONE
        features = merging_inst.ExtractFeatures()
        context = [(f, 1.0) for f in features]
        prediction = (self.classifier.predict(context))
        return prediction == 'True'


class MergingInst(object):
    def __init__(self, basic_edit_list, merge_loc):
        """1 <= merge_loc < len(basic_edit_list), Hypothesis is merging between basic_edit_list[merge_loc - 1] and basic_edit_list[merge_loc]"""
        self.basic_edit_list = basic_edit_list
        self.merge_loc = merge_loc

    def GetPrevEdit(self):
        return self.basic_edit_list[self.merge_loc - 1]

    def GetNextEdit(self):
        return self.basic_edit_list[self.merge_loc]

    def GetPrevEndAt(self):
        return self.basic_edit_list[self.merge_loc - 1].GetEndAt()

    def GetNextStartAt(self):
        return self.basic_edit_list[self.merge_loc].GetStartAt()

    def ExtractNUCLEFeatures(self):
        def SamePOSFeature(edit):
            orig_pos = edit.GetOrigPOS()
            rev_pos = edit.GetRevPOS()
            if orig_pos == rev_pos:
                return ["+".join(orig_pos)]
            else:
                return []

        def LOfCommonPrefix(s1, s2):
            l = 0
            while l < len(s1) and l < len(s2):
                if s1[l] != s2[l]:
                    break
                l += 1
            return l

        def GetLeastSuffix(s1, s2):
            l = LOfCommonPrefix(s1, s2)
            return (s1[l:].encode('ascii', 'ignore'), s2[l:].encode('ascii', 'ignore'))
        
        features = []
        # swanson feature
        if self.GetPrevEndAt() == self.GetNextStartAt():
            features.append('adjacent')

        x, y = self.GetPrevEndAt()
        nx, ny = self.GetNextStartAt()
        if (nx, ny) == (x+1, y+1):
             features.append('ONE_IN_MIDDLE')

        features.append('GAP_%d_%d' % (nx - x, ny - y))

        # l/r edit distance
        l_orig = self.GetPrevEdit().GetOrigPhrase()
        l_trg = self.GetPrevEdit().GetRevPhrase()
        l_edit_dist = CalculateEditDistance(l_orig, l_trg)
        features.append('LED=%d' % l_edit_dist)

        r_orig = self.GetNextEdit().GetOrigPhrase()
        r_trg = self.GetNextEdit().GetRevPhrase()
        r_edit_dist = CalculateEditDistance(r_orig, r_trg)
        features.append('RED=%d' % r_edit_dist)

        if ny - y == 0:
            features.append(('REVISED_TO=%s_%s' % (l_trg, r_trg)).encode('ascii', 'ignore'))
        features.append('L_LEAST_SUFF=%s_%s' % GetLeastSuffix(l_orig, l_trg))
        features.append('R_LEAST_SUFF=%s_%s' % GetLeastSuffix(r_orig, r_trg))

        features.append(('L_EDIT=%s_%s' % (l_orig, l_trg)).encode(
            'ascii', 'ignore'))
        features.append(('R_EDIT=%s_%s' % (r_orig, r_trg)).encode(
            'ascii', 'ignore'))

        # l in dictionary
        if len(l_orig) >= 0 and len(wordnet.synsets(l_orig)) == 0:
             features.append('LEFT_ORIG_OOV')

        if len(r_orig) >= 0 and len(wordnet.synsets(r_orig)) == 0:
             features.append('RIGHT_ORIG_OOV')

        if l_orig + r_orig == l_trg + r_trg:
             features.append('TWO_IDENTICAL')
             features.append('TWO_IDENTICAL_WORDS=%d' % len(
                  (l_orig + r_orig).split()))

        if any(l_orig == i.GetRevPhrase()
               for i in self.basic_edit_list[self.merge_loc:]):
             features.append('O_IDENTICAL_TO_LATER')

        if (l_orig + r_orig).endswith('ing') and (l_trg + r_trg).startswith('to'):
             features.append('ING_TO_TO')

        l_edit_type = self.GetPrevEdit().GetEditType()
        r_edit_type = self.GetNextEdit().GetEditType()
        features.append('LREDITTYPES=%s_%s' % (l_edit_type, r_edit_type))

        lpos_features = [
             "LPOS=%s" % p for p in SamePOSFeature(self.GetPrevEdit())]
        features.extend(lpos_features)
        if len(lpos_features) != 0:
             features.append('LPOSSAME')

        rpos_features = [
             "RPOS=%s" % p for p in SamePOSFeature(self.GetNextEdit())]
        features.extend(rpos_features)
        if len(rpos_features) != 0:
             features.append('RPOSSAME')

        if self.basic_edit_list[0].SentencesHaveIdenticalWordSets():
             features.append('SAMEWORDSET')

        return features


    def ExtractFeatures(self):
        return self.ExtractNUCLEFeatures()


class CorrectionExtractor(object):
    def __init__(self, classifier_location):
        self.merger = Merger(classifier_location)
        self.extractor = EditDistancWithMergerBuilder(self.merger)

    def ExtractAnnotations(self, original, revision):
        return self.extractor.ExtractAnnotations(original, revision)

class Selector(object):
    def __init__(self, classifier_location):
        self.classifier = maxent.MaxentModel()
        self.classifier.load(classifier_location)


    def predict(self, features):
        return self.classifier.predict(features)

class ErrorTypeInstance(object):
    def __init__(
        self, aligned_sent, error_type, to_pos_seq):
        self.aligned_sent = aligned_sent
        self.error_type = error_type
        self.to_pos_seq = to_pos_seq

        self.virt_to_pos_seq = ['<s>'] + self.to_pos_seq + ['</s>'] * 2
        self.virt_to_words = ['<s>'] + [
            t for f, t in self.aligned_sent if t is not None] + ['</s>'] * 2

    def GetPOSAt(self, i):
        return self.virt_to_pos_seq[i+1]

    def GetWordAt(self, i):
        return self.virt_to_words[i+1]

    def _HaveSameWords(self):
        orig_words = [f for f, t in self.aligned_sent if f is not None]
        trg_words = [t for f, t in self.aligned_sent if t is not None]
        if len(orig_words) != len(trg_words):
            return False
        return (sorted(orig_words) == sorted(trg_words))

    def GetPOSContextAt(self, t_ind, prefix=''):
        return set(['%sPOS_PREC(%s)POS_FOLLOW(%s)' % (
            prefix,
            self.GetPOSAt(t_ind - 1) ,self.GetPOSAt(t_ind + 1))])

    def GetMaxEntLine(self):
        try:
            line =  "%s %s" % (
                self.error_type, " ".join(self.ExtractFeatures()))
            return line
        except:
            print "encountered an error when extracting features:"
            print self.aligned_sent
            print self.error_type
            print self.to_pos_seq
            raise

    def ExtractFeatures(self):
        features = set()
        cur_targ_ind = 0

        orig_sent = []
        trg_sent = []

        n_edits = len([(f, t) for (f, t) in self.aligned_sent if f != t])
        
        for f, t in self.aligned_sent:
            if f is None:
                features.add('INS')
                features.add('INS(%s)' % t)
                if n_edits == 1:
                    features.update(self.GetPOSContextAt(cur_targ_ind, 'INS_'))
                cur_targ_ind += 1

                trg_sent.append(t)
            elif t is None:
                features.add('DEL')
                features.add('DEL(%s)' % f)
                if n_edits == 1:
                    features.update(self.GetPOSContextAt(cur_targ_ind, 'DEL_'))

                orig_sent.append(f)
            elif f != t:
                features.add('SUB')
                features.add('SUB(%s,%s)' % (f, t))

                char_align = EditDistanceAlign(f, t)
                char_unequal = [x != y for x, y in char_align]
                features.add('CHAR_EDITS(%d)' % sum(char_unequal))
                features.add("CPL(%d)" % char_unequal.index(True))
                features.add("PREV_W(%s)" % self.GetWordAt(cur_targ_ind - 1))
                features.add("SUB_POS(%s)" % self.GetPOSAt(cur_targ_ind))

                if n_edits == 1 and cur_targ_ind > 0:
                    features.add(
                        'SubPrevWord-%s' % self.GetWordAt(cur_targ_ind))

                f_stems = set([wnl.lemmatize(f, pos) for pos in all_pos])
                t_stems = set([wnl.lemmatize(t, pos) for pos in all_pos])

                isect = f_stems.intersection(t_stems)
                if len(isect) == 1:
                    features.add('SAME_STEM')
                    lem_len = len(list(isect)[0])
                    features.add('SUFFIXES(%s,%s)' % (f[lem_len:], t[lem_len:]))

                frm_in_dict = EngWordList.EngHasWord(f.lower()) and 'IN' or 'OUT' ##len(wordnet.synsets(f)) > 0 and 'IN' or 'OUT'
                to_in_dict = EngWordList.EngHasWord(t.lower()) and 'IN' or 'OUT' ##len(wordnet.synsets(t)) > 0 and 'IN' or 'OUT'
                features.add('%s-%s-DICT' % (frm_in_dict, to_in_dict))

                cur_targ_ind += 1
            else:
                cur_targ_ind += 1

        total_edits = sum(x != y for x, y in self.aligned_sent)
        features.add('N_EDITS(%d)' % total_edits)
        
        if self._HaveSameWords():
            features.add('SAMEWORDS')
        
        return list(features)

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

def ApplyCorrections(orig_surface, corrections):
    surfaces = orig_surface
    corrections = sorted(corrections)

    seq = AnnotatableSequence(surfaces)
    seq.SetOverlapAlarm(False)
    for (start, end, corr_as) in corrections:
        seq.Annotate(start, end, corr_as)
    segments = seq.GetSegments()
        
    result = []
    resulting_corrections = []

    for orig, rev in segments:
        if rev is None:
            result.extend(orig)
        else:
            result.append(rev)

    return (' '.join(result)).split()


def ExtractInstancesFromSentenceSurfaceAndCorrections(
        surface, corrections, pos_ac,
    builder = ErrorTypeInstance):
    after_apply = ApplyCorrections(
        surface, [(st, ed, corr_to) for tp, st, ed, corr_to in corrections])
    if len(after_apply) != len(pos_ac):
        raise ValueError("incorrect POS sequence %r for %r" % (
            pos_ac, after_apply))

    result = []
    for i, (corr_type, corr_start, corr_end, corr_to) in enumerate(corrections):
        all_other_corrections = corrections[:i] + corrections[i+1:]
        revision_result = ApplyCorrections(
            surface,
            [(st, ed, corr_to) for tp, st, ed, corr_to in all_other_corrections])
        align = EditDistanceAlign(revision_result, after_apply)

        result.append(builder(align, corr_type, pos_ac))
    return result

class CorrectionInstance(object):
    def __init__(self, error_type, features):
        self.error_type = error_type
        self.features = features

    @staticmethod
    def ConvertToString(unicode_str):
        return unicode_str.encode('utf-8', 'replace')

    def GetErrorType(self):
        return CorrectionInstance.ConvertToString(self.error_type)

    def GetFeatures(self):
        return map(CorrectionInstance.ConvertToString, self.features)

    def __str__(self):
        return "<CorrectionInstance: error_type=%r, features=%r>" % (
            self.GetErrorType(), self.GetFeatures())

class Model(object):
    def __init__(self, selector_model_path, merger_model_path):
        self.selector = Selector(selector_model_path)
        self.extractor = CorrectionExtractor(merger_model_path)

    def ExtractCorrections(self, sent1_words, sent2_words):
        original = sent1_words
        revision = sent2_words

        corrections = self.extractor.ExtractAnnotations(
            original, revision)
        corrections = [
            (None, st, ed, corr_to) for (st, ed, corr_to) in corrections]

        instances = ExtractInstancesFromSentenceSurfaceAndCorrections(
            original, corrections, TagSentence(revision))

        annotations = []
        for error_type_inst, (none, st, ed, corr_to) in zip(
            instances, corrections):
            annotations.append(
                (self.selector.predict(
                    [(CorrectionInstance.ConvertToString(w), 1.0) for w in error_type_inst.ExtractFeatures()]),
                 st,
                 ed,
                 corr_to
                 ))
        return annotations


    the_model = None
    @staticmethod
    def GetTheModel():
        if Model.the_model is None:
            Model.the_model = Model(selector_model_path, merger_model_path)
        return Model.the_model    

def ExtractCorrections(sent1_words, sent2_words):
    return Model.GetTheModel().ExtractCorrections(sent1_words, sent2_words)

if __name__ == "__main__":
    print ExtractCorrections('I like this .'.split(), 'I love this .'.split())
    print ExtractCorrections('I do not like this .'.split(), 'I love this .'.split())

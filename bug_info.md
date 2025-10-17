# Bug Classification Results

Total bugs classified: 431

## Summary

- **Functional bugs**: 293
- **Exceptional bugs**: 138
- **Errors**: 0

## Classification Results

| Project | Bug ID | Type | Bug Report | Root Causes | Modified Sources |
|---------|--------|------|------------|-------------|------------------|
| Chart | 1 | functional | 983 | 1: org.jfree.chart.renderer.category.junit.AbstractCategoryItemRendererTests::test2947660 | org.jfree.chart.renderer.category.AbstractCategoryItemRenderer |
| Chart | 2 | exceptional | 959 | 1: org.jfree.data.general.junit.DatasetUtilitiesTests::testBug2849731_2; 2: org.jfree.data.general.junit.DatasetUtilitiesTests::testBug2849731_3 | org.jfree.data.general.DatasetUtilities |
| Chart | 3 | functional | UNKNOWN | 1: org.jfree.data.time.junit.TimeSeriesTests::testCreateCopy3 | org.jfree.data.time.TimeSeries |
| Chart | 4 | exceptional | UNKNOWN | 22 cause(s) | org.jfree.chart.plot.XYPlot |
| Chart | 5 | exceptional | 862 | 1: org.jfree.data.xy.junit.XYSeriesTests::testBug1955483 | org.jfree.data.xy.XYSeries |
| Chart | 6 | functional | UNKNOWN | 1: org.jfree.chart.util.junit.ShapeListTests::testSerialization; 2: org.jfree.chart.util.junit.ShapeListTests::testEquals | org.jfree.chart.util.ShapeList |
| Chart | 7 | functional | UNKNOWN | 1: org.jfree.data.time.junit.TimePeriodValuesTests::testGetMaxMiddleIndex | org.jfree.data.time.TimePeriodValues |
| Chart | 8 | functional | UNKNOWN | 1: org.jfree.data.time.junit.WeekTests::testConstructor | org.jfree.data.time.Week |
| Chart | 9 | exceptional | 818 | 1: org.jfree.data.time.junit.TimeSeriesTests::testBug1864222 | org.jfree.data.time.TimeSeries |
| Chart | 10 | exceptional | UNKNOWN | 1: org.jfree.chart.imagemap.junit.StandardToolTipTagFragmentGeneratorTests::testGenerateURLFragment | org.jfree.chart.imagemap.StandardToolTipTagFragmentGenerator |
| Chart | 11 | functional | 868 | 1: org.jfree.chart.util.junit.ShapeUtilitiesTests::testEqualGeneralPaths | org.jfree.chart.util.ShapeUtilities |
| Chart | 12 | functional | 213 | 1: org.jfree.chart.plot.junit.MultiplePiePlotTests::testConstructor | org.jfree.chart.plot.MultiplePiePlot |
| Chart | 13 | exceptional | UNKNOWN | 1: org.jfree.chart.block.junit.BorderArrangementTests::testSizingWithWidthConstraint | org.jfree.chart.block.BorderArrangement |
| Chart | 14 | exceptional | UNKNOWN | 4 cause(s) | org.jfree.chart.plot.CategoryPlot; org.jfree.chart.plot.XYPlot |
| Chart | 15 | functional | UNKNOWN | 1: org.jfree.chart.plot.junit.PiePlot3DTests::testDrawWithNullDataset | org.jfree.chart.plot.PiePlot |
| Chart | 16 | functional | 834 | 8 cause(s) | org.jfree.data.category.DefaultIntervalCategoryDataset |
| Chart | 17 | exceptional | 803 | 1: org.jfree.data.time.junit.TimeSeriesTests::testBug1832432 | org.jfree.data.time.TimeSeries |
| Chart | 18 | functional | UNKNOWN | 4 cause(s) | org.jfree.data.DefaultKeyedValues; org.jfree.data.DefaultKeyedValues2D |
| Chart | 19 | functional | UNKNOWN | 1: org.jfree.chart.plot.junit.CategoryPlotTests::testGetRangeAxisIndex; 2: org.jfree.chart.plot.junit.CategoryPlotTests::testGetDomainAxisIndex | org.jfree.chart.plot.CategoryPlot |
| Chart | 20 | functional | UNKNOWN | 1: org.jfree.chart.plot.junit.ValueMarkerTests::test1808376 | org.jfree.chart.plot.ValueMarker |
| Chart | 21 | functional | UNKNOWN | 1: org.jfree.data.statistics.junit.DefaultBoxAndWhiskerCategoryDatasetTests::testGetRangeBounds | org.jfree.data.statistics.DefaultBoxAndWhiskerCategoryDataset |
| Chart | 22 | functional | UNKNOWN | 6 cause(s) | org.jfree.data.KeyedObjects2D |
| Chart | 23 | functional | UNKNOWN | 1: org.jfree.chart.renderer.category.junit.MinMaxCategoryRendererTests::testEquals | org.jfree.chart.renderer.category.MinMaxCategoryRenderer |
| Chart | 24 | exceptional | UNKNOWN | 1: org.jfree.chart.renderer.junit.GrayPaintScaleTests::testGetPaint | org.jfree.chart.renderer.GrayPaintScale |
| Chart | 25 | functional | UNKNOWN | 4 cause(s) | org.jfree.chart.renderer.category.StatisticalBarRenderer |
| Chart | 26 | functional | UNKNOWN | 22 cause(s) | org.jfree.chart.axis.Axis |
| Closure | 1 | functional | 253 | 8 cause(s) | com.google.javascript.jscomp.RemoveUnusedVars |
| Closure | 2 | exceptional | 884 | 1: com.google.javascript.jscomp.TypeCheckTest::testBadInterfaceExtendsNonExistentInterfaces | com.google.javascript.jscomp.TypeCheck |
| Closure | 3 | functional | 864 | 1: com.google.javascript.jscomp.FlowSensitiveInlineVariablesTest::testDoNotInlineCatchExpression1a; 2: com.google.javascript.jscomp.FlowSensitiveInlineVariablesTest::testDoNotInlineCatchExpression1; 3: com.google.javascript.jscomp.FlowSensitiveInlineVariablesTest::testDoNotInlineCatchExpression3 | com.google.javascript.jscomp.FlowSensitiveInlineVariables |
| Closure | 4 | functional | 873 | 1: com.google.javascript.jscomp.TypeCheckTest::testImplementsExtendsLoop; 2: com.google.javascript.jscomp.TypeCheckTest::testImplementsLoop; 3: com.google.javascript.jscomp.TypeCheckTest::testConversionFromInterfaceToRecursiveConstructor | com.google.javascript.rhino.jstype.NamedType |
| Closure | 5 | functional | 851 | 1: com.google.javascript.jscomp.InlineObjectLiteralsTest::testNoInlineDeletedProperties | com.google.javascript.jscomp.InlineObjectLiterals |
| Closure | 6 | functional | 635 | 1: com.google.javascript.jscomp.LooseTypeCheckTest::testTypeRedefinition; 2: com.google.javascript.jscomp.TypeCheckTest::testIssue635b; 3: com.google.javascript.jscomp.TypeCheckTest::testTypeRedefinition | com.google.javascript.jscomp.TypeValidator |
| Closure | 7 | functional | 841 | 1: com.google.javascript.jscomp.ClosureReverseAbstractInterpreterTest::testGoogIsFunction2; 2: com.google.javascript.jscomp.SemanticReverseAbstractInterpreterTest::testTypeof3 | com.google.javascript.jscomp.type.ChainableReverseAbstractInterpreter |
| Closure | 8 | functional | 820 | 1: com.google.javascript.jscomp.CollapseVariableDeclarationsTest::testIssue820 | com.google.javascript.jscomp.CollapseVariableDeclarations |
| Closure | 9 | exceptional | 824 | 1: com.google.javascript.jscomp.ProcessCommonJSModulesTest::testGuessModuleName | com.google.javascript.jscomp.ProcessCommonJSModules |
| Closure | 10 | functional | 821 | 1: com.google.javascript.jscomp.PeepholeFoldConstantsTest::testIssue821 | com.google.javascript.jscomp.NodeUtil |
| Closure | 11 | functional | 810 | 1: com.google.javascript.jscomp.TypeCheckTest::testGetprop4; 2: com.google.javascript.jscomp.TypeCheckTest::testIssue810 | com.google.javascript.jscomp.TypeCheck |
| Closure | 12 | functional | 794 | 1: com.google.javascript.jscomp.FlowSensitiveInlineVariablesTest::testIssue794b | com.google.javascript.jscomp.MaybeReachingVariableUse |
| Closure | 13 | functional | 787 | 1: com.google.javascript.jscomp.IntegrationTest::testIssue787 | com.google.javascript.jscomp.PeepholeOptimizationsPass |
| Closure | 14 | functional | 779 | 1: com.google.javascript.jscomp.CheckMissingReturnTest::testIssue779; 2: com.google.javascript.jscomp.ControlFlowAnalysisTest::testDeepNestedFinally; 3: com.google.javascript.jscomp.ControlFlowAnalysisTest::testDeepNestedBreakwithFinally | com.google.javascript.jscomp.ControlFlowAnalysis |
| Closure | 15 | functional | 773 | 1: com.google.javascript.jscomp.FlowSensitiveInlineVariablesTest::testSimpleForIn | com.google.javascript.jscomp.FlowSensitiveInlineVariables |
| Closure | 16 | functional | 772 | 1: com.google.javascript.jscomp.IntegrationTest::testIssue772; 2: com.google.javascript.jscomp.ScopedAliasesTest::testIssue772 | com.google.javascript.jscomp.ScopedAliases |
| Closure | 17 | exceptional | 688 | 1: com.google.javascript.jscomp.TypeCheckTest::testIssue688 | com.google.javascript.jscomp.TypedScopeCreator |
| Closure | 18 | functional | 768 | 1: com.google.javascript.jscomp.IntegrationTest::testDependencySorting | com.google.javascript.jscomp.Compiler |
| Closure | 19 | exceptional | 769 | 1: com.google.javascript.jscomp.TypeInferenceTest::testNoThisInference | com.google.javascript.jscomp.type.ChainableReverseAbstractInterpreter |
| Closure | 20 | functional | 759 | 1: com.google.javascript.jscomp.PeepholeSubstituteAlternateSyntaxTest::testSimpleFunctionCall | com.google.javascript.jscomp.PeepholeSubstituteAlternateSyntax |
| Closure | 21 | functional | 753 | 1: com.google.javascript.jscomp.CheckSideEffectsTest::testUselessCode | com.google.javascript.jscomp.CheckSideEffects |
| Closure | 22 | functional | 753 | 1: com.google.javascript.jscomp.CheckSideEffectsTest::testUselessCode | com.google.javascript.jscomp.CheckSideEffects |
| Closure | 23 | functional | 747 | 1: com.google.javascript.jscomp.PeepholeFoldConstantsTest::testFoldGetElem | com.google.javascript.jscomp.PeepholeFoldConstants |
| Closure | 24 | functional | 737 | 1: com.google.javascript.jscomp.ScopedAliasesTest::testNonAliasLocal | com.google.javascript.jscomp.ScopedAliases |
| Closure | 25 | exceptional | 729 | 1: com.google.javascript.jscomp.TypeInferenceTest::testBackwardsInferenceNew | com.google.javascript.jscomp.TypeInference |
| Closure | 26 | functional | 732 | 7 cause(s) | com.google.javascript.jscomp.ProcessCommonJSModules |
| Closure | 27 | exceptional | 727 | 1: com.google.javascript.rhino.IRTest::testIssue727_1; 2: com.google.javascript.rhino.IRTest::testIssue727_2; 3: com.google.javascript.rhino.IRTest::testIssue727_3 | com.google.javascript.rhino.IR |
| Closure | 28 | functional | 728 | 1: com.google.javascript.jscomp.InlineCostEstimatorTest::testCost; 2: com.google.javascript.jscomp.InlineFunctionsTest::testIssue728 | com.google.javascript.jscomp.InlineCostEstimator |
| Closure | 29 | functional | 724 | 5 cause(s) | com.google.javascript.jscomp.InlineObjectLiterals |
| Closure | 30 | functional | 698 | 1: com.google.javascript.jscomp.FlowSensitiveInlineVariablesTest::testInlineAcrossSideEffect1; 2: com.google.javascript.jscomp.FlowSensitiveInlineVariablesTest::testCanInlineAcrossNoSideEffect; 3: com.google.javascript.jscomp.FlowSensitiveInlineVariablesTest::testIssue698 | com.google.javascript.jscomp.FlowSensitiveInlineVariables; com.google.javascript.jscomp.MustBeReachingVariableDef |
| Closure | 31 | functional | 703 | 1: com.google.javascript.jscomp.CommandLineRunnerTest::testDependencySortingWhitespaceMode | com.google.javascript.jscomp.Compiler |
| Closure | 32 | exceptional | 701 | 4 cause(s) | com.google.javascript.jscomp.parsing.JsDocInfoParser |
| Closure | 33 | functional | 700 | 1: com.google.javascript.jscomp.TypeCheckTest::testIssue700 | com.google.javascript.rhino.jstype.PrototypeObjectType |
| Closure | 34 | exceptional | 691 | 1: com.google.javascript.jscomp.CodePrinterTest::testManyAdds | com.google.javascript.jscomp.CodeGenerator; com.google.javascript.jscomp.CodePrinter |
| Closure | 35 | functional | 669 | 1: com.google.javascript.jscomp.TypeCheckTest::testIssue669 | com.google.javascript.jscomp.TypeInference |
| Closure | 36 | functional | 668 | 1: com.google.javascript.jscomp.IntegrationTest::testSingletonGetter1 | com.google.javascript.jscomp.InlineVariables |
| Closure | 37 | exceptional | 663 | 1: com.google.javascript.jscomp.IntegrationTest::testIncompleteFunction | com.google.javascript.jscomp.NodeTraversal; com.google.javascript.jscomp.parsing.IRFactory |
| Closure | 38 | exceptional | 657 | 1: com.google.javascript.jscomp.CodePrinterTest::testMinusNegativeZero | com.google.javascript.jscomp.CodeConsumer |
| Closure | 39 | exceptional | 643 | 1: com.google.javascript.rhino.jstype.RecordTypeTest::testRecursiveRecord; 2: com.google.javascript.rhino.jstype.RecordTypeTest::testLongToString | com.google.javascript.rhino.jstype.PrototypeObjectType |
| Closure | 40 | functional | 284 | 1: com.google.javascript.jscomp.IntegrationTest::testIssue284; 2: com.google.javascript.jscomp.NameAnalyzerTest::testIssue284 | com.google.javascript.jscomp.NameAnalyzer |
| Closure | 41 | functional | 368 | 1: com.google.javascript.jscomp.LooseTypeCheckTest::testMethodInference6; 2: com.google.javascript.jscomp.TypeCheckTest::testIssue368; 3: com.google.javascript.jscomp.TypeCheckTest::testMethodInference6 | com.google.javascript.jscomp.FunctionTypeBuilder |
| Closure | 42 | functional | 644 | 1: com.google.javascript.jscomp.parsing.ParserTest::testForEach | com.google.javascript.jscomp.parsing.IRFactory |
| Closure | 43 | exceptional | 314 | 1: com.google.javascript.jscomp.TypeCheckTest::testLends10; 2: com.google.javascript.jscomp.TypeCheckTest::testLends11 | com.google.javascript.jscomp.TypedScopeCreator |
| Closure | 44 | exceptional | 620 | 1: com.google.javascript.jscomp.CodePrinterTest::testIssue620 | com.google.javascript.jscomp.CodeConsumer |
| Closure | 45 | functional | 618 | 1: com.google.javascript.jscomp.RemoveUnusedVarsTest::testIssue618_1 | com.google.javascript.jscomp.RemoveUnusedVars |
| Closure | 46 | functional | 603 | 1: com.google.javascript.rhino.jstype.JSTypeTest::testRecordTypeLeastSuperType2; 2: com.google.javascript.rhino.jstype.JSTypeTest::testRecordTypeLeastSuperType3; 3: com.google.javascript.rhino.jstype.RecordTypeTest::testSupAndInf | com.google.javascript.rhino.jstype.RecordType |
| Closure | 47 | functional | 575 | 16 cause(s) | com.google.debugging.sourcemap.SourceMapConsumerV3; com.google.javascript.jscomp.SourceMap |
| Closure | 48 | functional | 586 | 1: com.google.javascript.jscomp.TypeCheckTest::testIssue586 | com.google.javascript.jscomp.TypedScopeCreator |
| Closure | 49 | functional | 539 | 66 cause(s) | com.google.javascript.jscomp.MakeDeclaredNamesUnique |
| Closure | 50 | functional | 558 | 1: com.google.javascript.jscomp.PeepholeReplaceKnownMethodsTest::testStringJoinAdd; 2: com.google.javascript.jscomp.PeepholeReplaceKnownMethodsTest::testNoStringJoin | com.google.javascript.jscomp.PeepholeReplaceKnownMethods |
| Closure | 51 | exceptional | 582 | 1: com.google.javascript.jscomp.CodePrinterTest::testIssue582 | com.google.javascript.jscomp.CodeConsumer |
| Closure | 52 | exceptional | 569 | 1: com.google.javascript.jscomp.CodePrinterTest::testNumericKeys | com.google.javascript.jscomp.CodeGenerator |
| Closure | 53 | exceptional | 545 | 1: com.google.javascript.jscomp.InlineObjectLiteralsTest::testBug545 | com.google.javascript.jscomp.InlineObjectLiterals |
| Closure | 54 | exceptional | 537 | 1: com.google.javascript.jscomp.TypeCheckTest::testIssue537a; 2: com.google.javascript.jscomp.TypeCheckTest::testIssue537b; 3: com.google.javascript.jscomp.TypedScopeCreatorTest::testPropertyOnUnknownSuperClass2 | com.google.javascript.jscomp.TypedScopeCreator; com.google.javascript.rhino.jstype.FunctionType |
| Closure | 55 | exceptional | 538 | 1: com.google.javascript.jscomp.FunctionRewriterTest::testIssue538 | com.google.javascript.jscomp.FunctionRewriter |
| Closure | 56 | functional | 511 | 1: com.google.javascript.jscomp.JSCompilerSourceExcerptProviderTest::testExceptNoNewLine; 2: com.google.javascript.jscomp.JsMessageExtractorTest::testSyntaxError1; 3: com.google.javascript.jscomp.JsMessageExtractorTest::testSyntaxError2 | com.google.javascript.jscomp.SourceFile |
| Closure | 57 | functional | 530 | 1: com.google.javascript.jscomp.ClosureCodingConventionTest::testRequire | com.google.javascript.jscomp.ClosureCodingConvention |
| Closure | 58 | exceptional | 528 | 1: com.google.javascript.jscomp.LiveVariableAnalysisTest::testExpressionInForIn | com.google.javascript.jscomp.LiveVariablesAnalysis |
| Closure | 59 | functional | 521 | 1: com.google.javascript.jscomp.CommandLineRunnerTest::testCheckGlobalThisOff | com.google.javascript.jscomp.Compiler |
| Closure | 60 | functional | 504 | 1: com.google.javascript.jscomp.CommandLineRunnerTest::testIssue504; 2: com.google.javascript.jscomp.NodeUtilTest::testGetBooleanValue | com.google.javascript.jscomp.NodeUtil |
| Closure | 61 | functional | 501 | 1: com.google.javascript.jscomp.PeepholeRemoveDeadCodeTest::testCall1; 2: com.google.javascript.jscomp.PeepholeRemoveDeadCodeTest::testCall2; 3: com.google.javascript.jscomp.PeepholeRemoveDeadCodeTest::testRemoveUselessOps | com.google.javascript.jscomp.NodeUtil |
| Closure | 62 | exceptional | 487 | 1: com.google.javascript.jscomp.LightweightMessageFormatterTest::testFormatErrorSpaceEndOfLine1; 2: com.google.javascript.jscomp.LightweightMessageFormatterTest::testFormatErrorSpaceEndOfLine2 | com.google.javascript.jscomp.LightweightMessageFormatter |
| Closure | 64 | functional | 489 | 1: com.google.javascript.jscomp.CommandLineRunnerTest::testES5StrictUseStrictMultipleInputs | com.google.javascript.jscomp.Compiler |
| Closure | 65 | exceptional | 486 | 1: com.google.javascript.jscomp.CodePrinterTest::testZero | com.google.javascript.jscomp.CodeGenerator |
| Closure | 66 | functional | 482 | 1: com.google.javascript.jscomp.TypeCheckTest::testGetTypedPercent5; 2: com.google.javascript.jscomp.TypeCheckTest::testGetTypedPercent6 | com.google.javascript.jscomp.TypeCheck |
| Closure | 67 | functional | 459 | 1: com.google.javascript.jscomp.RemoveUnusedPrototypePropertiesTest::testAliasing7 | com.google.javascript.jscomp.AnalyzePrototypeProperties |
| Closure | 68 | functional | 477 | 1: com.google.javascript.jscomp.parsing.JsDocInfoParserTest::testIssue477 | com.google.javascript.jscomp.parsing.JsDocInfoParser |
| Closure | 69 | functional | 440 | 1: com.google.javascript.jscomp.TypeCheckTest::testThisTypeOfFunction2; 2: com.google.javascript.jscomp.TypeCheckTest::testThisTypeOfFunction3; 3: com.google.javascript.jscomp.TypeCheckTest::testThisTypeOfFunction4 | com.google.javascript.jscomp.TypeCheck |
| Closure | 70 | functional | 433 | 5 cause(s) | com.google.javascript.jscomp.TypedScopeCreator |
| Closure | 71 | functional | 254 | 1: com.google.javascript.jscomp.CheckAccessControlsTest::testNoPrivateAccessForProperties6; 2: com.google.javascript.jscomp.CheckAccessControlsTest::testNoPrivateAccessForProperties8 | com.google.javascript.jscomp.CheckAccessControls |
| Closure | 72 | functional | 435 | 1: com.google.javascript.jscomp.InlineFunctionsTest::testInlineFunctions31 | com.google.javascript.jscomp.FunctionToBlockMutator; com.google.javascript.jscomp.RenameLabels |
| Closure | 73 | exceptional | 416 | 1: com.google.javascript.jscomp.CodePrinterTest::testUnicode | com.google.javascript.jscomp.CodeGenerator |
| Closure | 74 | functional | 413 | 1: com.google.javascript.jscomp.PeepholeFoldConstantsTest::testFoldComparison3; 2: com.google.javascript.jscomp.PeepholeFoldConstantsTest::testInvertibleOperators; 3: com.google.javascript.jscomp.PeepholeFoldConstantsTest::testCommutativeOperators | com.google.javascript.jscomp.PeepholeFoldConstants |
| Closure | 75 | functional | 395 | 1: com.google.javascript.jscomp.PeepholeFoldConstantsTest::testIEString | com.google.javascript.jscomp.NodeUtil |
| Closure | 76 | functional | 384 | 4 cause(s) | com.google.javascript.jscomp.DeadAssignmentsElimination |
| Closure | 77 | exceptional | 383 | 1: com.google.javascript.jscomp.CodePrinterTest::testZero | com.google.javascript.jscomp.CodeGenerator |
| Closure | 78 | functional | 381 | 1: com.google.javascript.jscomp.PeepholeFoldConstantsTest::testFoldArithmetic | com.google.javascript.jscomp.PeepholeFoldConstants |
| Closure | 79 | functional | 367 | 5 cause(s) | com.google.javascript.jscomp.Normalize; com.google.javascript.jscomp.VarCheck |
| Closure | 80 | functional | 364 | 1: com.google.javascript.jscomp.NodeUtilTest::testIsBooleanResult; 2: com.google.javascript.jscomp.NodeUtilTest::testLocalValue1 | com.google.javascript.jscomp.NodeUtil |
| Closure | 81 | functional | 251 | 1: com.google.javascript.jscomp.parsing.ParserTest::testUnnamedFunctionStatement | com.google.javascript.jscomp.parsing.IRFactory |
| Closure | 82 | functional | 301 | 1: com.google.javascript.jscomp.TypeCheckTest::testIssue301; 2: com.google.javascript.rhino.jstype.FunctionTypeTest::testEmptyFunctionTypes | com.google.javascript.rhino.jstype.JSType |
| Closure | 83 | functional | 319 | 1: com.google.javascript.jscomp.CommandLineRunnerTest::testVersionFlag2 | com.google.javascript.jscomp.CommandLineRunner |
| Closure | 84 | functional | 215 | 1: com.google.javascript.jscomp.parsing.ParserTest::testDestructuringAssignForbidden4 | com.google.javascript.jscomp.parsing.IRFactory |
| Closure | 85 | functional | 311 | 1: com.google.javascript.jscomp.UnreachableCodeEliminationTest::testCascadedRemovalOfUnlessUnconditonalJumps; 2: com.google.javascript.jscomp.UnreachableCodeEliminationTest::testIssue311 | com.google.javascript.jscomp.UnreachableCodeElimination |
| Closure | 86 | functional | 303 | 7 cause(s) | com.google.javascript.jscomp.NodeUtil |
| Closure | 87 | functional | 291 | 1: com.google.javascript.jscomp.PeepholeSubstituteAlternateSyntaxTest::testIssue291 | com.google.javascript.jscomp.PeepholeSubstituteAlternateSyntax |
| Closure | 88 | functional | 297 | 7 cause(s) | com.google.javascript.jscomp.DeadAssignmentsElimination |
| Closure | 89 | functional | 289 | 8 cause(s) | com.google.javascript.jscomp.CollapseProperties; com.google.javascript.jscomp.GlobalNamespace |
| Closure | 90 | functional | 274 | 1: com.google.javascript.jscomp.TypeCheckTest::testBackwardsTypedefUse8; 2: com.google.javascript.jscomp.TypeCheckTest::testBackwardsTypedefUse9 | com.google.javascript.jscomp.FunctionTypeBuilder; com.google.javascript.rhino.jstype.FunctionType |
| Closure | 91 | functional | 248 | 1: com.google.javascript.jscomp.CheckGlobalThisTest::testLendsAnnotation3 | com.google.javascript.jscomp.CheckGlobalThis |
| Closure | 92 | functional | 261 | 1: com.google.javascript.jscomp.ProcessClosurePrimitivesTest::testProvideInIndependentModules4 | com.google.javascript.jscomp.ProcessClosurePrimitives |
| Closure | 94 | functional | 255 | 1: com.google.javascript.jscomp.NodeUtilTest::testValidDefine; 2: com.google.javascript.jscomp.ProcessDefinesTest::testOverridingString1; 3: com.google.javascript.jscomp.ProcessDefinesTest::testOverridingString3 | com.google.javascript.jscomp.NodeUtil |
| Closure | 95 | functional | 66 | 1: com.google.javascript.jscomp.TypeCheckTest::testQualifiedNameInference5; 2: com.google.javascript.jscomp.TypedScopeCreatorTest::testGlobalQualifiedNameInLocalScope | com.google.javascript.jscomp.TypedScopeCreator |
| Closure | 96 | functional | 229 | 1: com.google.javascript.jscomp.TypeCheckTest::testFunctionArguments16 | com.google.javascript.jscomp.TypeCheck |
| Closure | 97 | functional | 200 | 1: com.google.javascript.jscomp.PeepholeFoldConstantsTest::testFoldBitShifts | com.google.javascript.jscomp.PeepholeFoldConstants |
| Closure | 98 | functional | 174 | 1: com.google.javascript.jscomp.InlineVariablesTest::testNoInlineAliasesInLoop | com.google.javascript.jscomp.ReferenceCollectingCallback |
| Closure | 99 | functional | 125 | 1: com.google.javascript.jscomp.CheckGlobalThisTest::testPropertyOfMethod; 2: com.google.javascript.jscomp.CheckGlobalThisTest::testMethod4; 3: com.google.javascript.jscomp.CheckGlobalThisTest::testInterface1 | com.google.javascript.jscomp.CheckGlobalThis |
| Closure | 100 | functional | 144 | 9 cause(s) | com.google.javascript.jscomp.CheckGlobalThis |
| Closure | 101 | functional | 130 | 1: com.google.javascript.jscomp.CommandLineRunnerTest::testProcessClosurePrimitives | com.google.javascript.jscomp.CommandLineRunner |
| Closure | 102 | functional | 115 | 1: com.google.javascript.jscomp.CompilerRunnerTest::testIssue115 | com.google.javascript.jscomp.Normalize |
| Closure | 103 | functional | 113 | 1: com.google.javascript.jscomp.CheckUnreachableCodeTest::testInstanceOfThrowsException; 2: com.google.javascript.jscomp.ControlFlowAnalysisTest::testInstanceOf; 3: com.google.javascript.jscomp.DisambiguatePropertiesTest::testSupertypeReferenceOfSubtypeProperty | com.google.javascript.jscomp.ControlFlowAnalysis; com.google.javascript.jscomp.DisambiguateProperties |
| Closure | 104 | functional | 114 | 1: com.google.javascript.rhino.jstype.UnionTypeTest::testGreatestSubtypeUnionTypes5 | com.google.javascript.rhino.jstype.UnionType |
| Closure | 105 | functional | 106 | 1: com.google.javascript.jscomp.FoldConstantsTest::testStringJoinAdd | com.google.javascript.jscomp.FoldConstants |
| Closure | 106 | functional | 19 | 4 cause(s) | com.google.javascript.jscomp.GlobalNamespace; com.google.javascript.rhino.JSDocInfoBuilder |
| Closure | 107 | functional | 1135 | 1: com.google.javascript.jscomp.CommandLineRunnerTest::testGetMsgWiringNoWarnings | com.google.javascript.jscomp.CommandLineRunner |
| Closure | 108 | exceptional | 1144 | 1: com.google.javascript.jscomp.ScopedAliasesTest::testIssue1144 | com.google.javascript.jscomp.ScopedAliases |
| Closure | 109 | functional | 1105 | 1: com.google.javascript.jscomp.parsing.JsDocInfoParserTest::testStructuralConstructor2; 2: com.google.javascript.jscomp.parsing.JsDocInfoParserTest::testStructuralConstructor3 | com.google.javascript.jscomp.parsing.JsDocInfoParser |
| Closure | 110 | functional | 1111 | 1: com.google.javascript.jscomp.ScopedAliasesTest::testHoistedFunctionDeclaration; 2: com.google.javascript.jscomp.ScopedAliasesTest::testFunctionDeclaration | com.google.javascript.jscomp.ScopedAliases; com.google.javascript.rhino.Node |
| Closure | 111 | functional | 1114 | 1: com.google.javascript.jscomp.ClosureReverseAbstractInterpreterTest::testGoogIsArray2 | com.google.javascript.jscomp.type.ClosureReverseAbstractInterpreter |
| Closure | 112 | functional | 1058 | 1: com.google.javascript.jscomp.TypeCheckTest::testIssue1058; 2: com.google.javascript.jscomp.TypeCheckTest::testTemplatized11 | com.google.javascript.jscomp.TypeInference |
| Closure | 113 | functional | 1079 | 1: com.google.javascript.jscomp.VarCheckTest::testNoUndeclaredVarWhenUsingClosurePass | com.google.javascript.jscomp.ProcessClosurePrimitives |
| Closure | 114 | functional | 1085 | 1: com.google.javascript.jscomp.NameAnalyzerTest::testAssignWithCall | com.google.javascript.jscomp.NameAnalyzer |
| Closure | 115 | functional | 1101 | 5 cause(s) | com.google.javascript.jscomp.FunctionInjector |
| Closure | 116 | functional | 1101 | 8 cause(s) | com.google.javascript.jscomp.FunctionInjector |
| Closure | 117 | exceptional | 1047 | 1: com.google.javascript.jscomp.TypeCheckTest::testIssue1047 | com.google.javascript.jscomp.TypeValidator |
| Closure | 118 | functional | 1024 | 1: com.google.javascript.jscomp.DisambiguatePropertiesTest::testOneType4; 2: com.google.javascript.jscomp.DisambiguatePropertiesTest::testTwoTypes4 | com.google.javascript.jscomp.DisambiguateProperties |
| Closure | 119 | functional | 1070 | 1: com.google.javascript.jscomp.CheckGlobalNamesTest::testGlobalCatch | com.google.javascript.jscomp.GlobalNamespace |
| Closure | 120 | functional | 1053 | 1: com.google.javascript.jscomp.InlineVariablesTest::testExternalIssue1053 | com.google.javascript.jscomp.ReferenceCollectingCallback |
| Closure | 121 | functional | 1053 | 1: com.google.javascript.jscomp.InlineVariablesTest::testExternalIssue1053 | com.google.javascript.jscomp.InlineVariables |
| Closure | 122 | functional | 1037 | 1: com.google.javascript.jscomp.parsing.ParserTest::testSuspiciousBlockCommentWarning3; 2: com.google.javascript.jscomp.parsing.ParserTest::testSuspiciousBlockCommentWarning4; 3: com.google.javascript.jscomp.parsing.ParserTest::testSuspiciousBlockCommentWarning5 | com.google.javascript.jscomp.parsing.IRFactory |
| Closure | 123 | exceptional | 1033 | 1: com.google.javascript.jscomp.CodePrinterTest::testPrintInOperatorInForLoop | com.google.javascript.jscomp.CodeGenerator |
| Closure | 124 | functional | 1017 | 1: com.google.javascript.jscomp.ExploitAssignsTest::testIssue1017 | com.google.javascript.jscomp.ExploitAssigns |
| Closure | 125 | exceptional | 1002 | 1: com.google.javascript.jscomp.TypeCheckTest::testIssue1002 | com.google.javascript.jscomp.TypeCheck |
| Closure | 126 | functional | 936 | 1: com.google.javascript.jscomp.MinimizeExitPointsTest::testDontRemoveBreakInTryFinally; 2: com.google.javascript.jscomp.MinimizeExitPointsTest::testFunctionReturnOptimization | com.google.javascript.jscomp.MinimizeExitPoints |
| Closure | 127 | functional | 936 | 6 cause(s) | com.google.javascript.jscomp.UnreachableCodeElimination |
| Closure | 128 | exceptional | 942 | 1: com.google.javascript.jscomp.CodePrinterTest::testIssue942 | com.google.javascript.jscomp.CodeGenerator |
| Closure | 129 | functional | 937 | 1: com.google.javascript.jscomp.IntegrationTest::testIssue937 | com.google.javascript.jscomp.PrepareAst |
| Closure | 130 | functional | 931 | 1: com.google.javascript.jscomp.CollapsePropertiesTest::testIssue931 | com.google.javascript.jscomp.CollapseProperties |
| Closure | 131 | functional | 921 | 1: com.google.javascript.jscomp.ConvertToDottedPropertiesTest::testQuotedProps; 2: com.google.javascript.jscomp.ConvertToDottedPropertiesTest::testDoNotConvert | com.google.javascript.rhino.TokenStream |
| Closure | 132 | functional | 925 | 1: com.google.javascript.jscomp.PeepholeSubstituteAlternateSyntaxTest::testIssue925 | com.google.javascript.jscomp.PeepholeSubstituteAlternateSyntax |
| Closure | 133 | exceptional | 919 | 1: com.google.javascript.jscomp.parsing.JsDocInfoParserTest::testTextExtents | com.google.javascript.jscomp.parsing.JsDocInfoParser |
| Closure | 134 | functional | 86 | 1: com.google.javascript.jscomp.AmbiguatePropertiesTest::testImplementsAndExtends; 2: com.google.javascript.jscomp.TypeCheckTest::testIssue86 | com.google.javascript.jscomp.AmbiguateProperties; com.google.javascript.jscomp.TypedScopeCreator |
| Closure | 135 | functional | 59 | 1: com.google.javascript.jscomp.DevirtualizePrototypeMethodsTest::testRewritePrototypeMethods2; 2: com.google.javascript.jscomp.TypeCheckTest::testGoodExtends9 | com.google.javascript.jscomp.DevirtualizePrototypeMethods; com.google.javascript.rhino.jstype.FunctionType |
| Closure | 136 | functional | 103 | 4 cause(s) | com.google.javascript.jscomp.MethodCompilerPass; com.google.javascript.jscomp.RenameVars |
| Closure | 137 | functional | 124 | 5 cause(s) | com.google.javascript.jscomp.MakeDeclaredNamesUnique; com.google.javascript.jscomp.NodeUtil; com.google.javascript.jscomp.Normalize |
| Closure | 138 | functional | 124 | 5 cause(s) | com.google.javascript.jscomp.ClosureReverseAbstractInterpreter; com.google.javascript.jscomp.TypeInference |
| Closure | 139 | functional | 33 | 1: com.google.javascript.jscomp.NormalizeTest::testNormalizeFunctionDeclarations; 2: com.google.javascript.jscomp.NormalizeTest::testRemoveDuplicateVarDeclarations3; 3: com.google.javascript.jscomp.NormalizeTest::testMoveFunctions2 | com.google.javascript.jscomp.Normalize |
| Closure | 140 | functional | 126 | 1: com.google.javascript.jscomp.CrossModuleCodeMotionTest::testEmptyModule | com.google.javascript.jscomp.Compiler |
| Closure | 141 | functional | 116 | 8 cause(s) | com.google.javascript.jscomp.NodeUtil; com.google.javascript.jscomp.PureFunctionIdentifier |
| Closure | 142 | functional | 58 | 1: com.google.javascript.jscomp.CoalesceVariableNamesTest::testParameter4; 2: com.google.javascript.jscomp.parsing.JsDocInfoParserTest::testParseLicenseWithAnnotation | com.google.javascript.jscomp.CoalesceVariableNames; com.google.javascript.jscomp.parsing.JsDocInfoParser |
| Closure | 143 | functional | 139 | 1: com.google.javascript.jscomp.CommandLineRunnerTest::testDefineFlag3; 2: com.google.javascript.jscomp.RemoveConstantExpressionsTest::testCall1; 3: com.google.javascript.jscomp.RemoveConstantExpressionsTest::testNew1 | com.google.javascript.jscomp.AbstractCommandLineRunner; com.google.javascript.jscomp.RemoveConstantExpressions |
| Closure | 144 | functional | 143 | 84 cause(s) | 4 class(es) |
| Closure | 145 | exceptional | 190 | 1: com.google.javascript.jscomp.CodePrinterTest::testFunctionSafariCompatiblity; 2: com.google.javascript.jscomp.CodePrinterTest::testDoLoopIECompatiblity | com.google.javascript.jscomp.CodeGenerator |
| Closure | 146 | functional | 172 | 1: com.google.javascript.jscomp.SemanticReverseAbstractInterpreterTest::testEqCondition4 | com.google.javascript.rhino.jstype.JSType |
| Closure | 147 | functional | 182 | 1: com.google.javascript.jscomp.CheckGlobalThisTest::testIssue182a; 2: com.google.javascript.jscomp.CheckGlobalThisTest::testIssue182b; 3: com.google.javascript.jscomp.RuntimeTypeCheckTest::testValueWithInnerFn | com.google.javascript.jscomp.CheckGlobalThis; com.google.javascript.jscomp.RuntimeTypeCheck |
| Closure | 148 | functional | 196 | 6 cause(s) | com.google.javascript.jscomp.PeepholeFoldConstants; com.google.javascript.jscomp.SourceMap |
| Closure | 149 | functional | 205 | 1: com.google.javascript.jscomp.CommandLineRunnerTest::testCharSetExpansion | 4 class(es) |
| Closure | 150 | functional | 61 | 1: com.google.javascript.jscomp.TypedScopeCreatorTest::testNamespacedFunctionStubLocal; 2: com.google.javascript.jscomp.TypedScopeCreatorTest::testCollectedFunctionStubLocal | com.google.javascript.jscomp.TypedScopeCreator |
| Closure | 151 | functional | 74 | 1: com.google.javascript.jscomp.CommandLineRunnerTest::testVersionFlag | com.google.javascript.jscomp.CommandLineRunner |
| Closure | 152 | exceptional | 268 | 1: com.google.javascript.jscomp.TypeCheckTest::testBackwardsTypedefUse1; 2: com.google.javascript.jscomp.TypeCheckTest::testBackwardsTypedefUse2; 3: com.google.javascript.jscomp.TypeCheckTest::testBackwardsTypedefUse3 | com.google.javascript.rhino.jstype.FunctionType |
| Closure | 153 | functional | 290 | 1: com.google.javascript.jscomp.NormalizeTest::testDuplicateVarInExterns; 2: com.google.javascript.jscomp.NormalizeTest::testMakeLocalNamesUnique | com.google.javascript.jscomp.Normalize; com.google.javascript.jscomp.SyntacticScopeCreator |
| Closure | 154 | functional | 204 | 1: com.google.javascript.jscomp.TypeCheckTest::testInterfaceInheritanceCheck12 | com.google.javascript.jscomp.TypeCheck; com.google.javascript.jscomp.TypeValidator |
| Closure | 155 | functional | 378 | 7 cause(s) | com.google.javascript.jscomp.InlineVariables; com.google.javascript.jscomp.ReferenceCollectingCallback; com.google.javascript.jscomp.Scope |
| Closure | 156 | functional | 389 | 1: com.google.javascript.jscomp.CollapsePropertiesTest::testAliasedTopLevelEnum; 2: com.google.javascript.jscomp.CollapsePropertiesTest::testIssue389 | com.google.javascript.jscomp.CollapseProperties |
| Closure | 157 | functional | 347 | 12 cause(s) | com.google.javascript.jscomp.CodeGenerator; com.google.javascript.jscomp.parsing.IRFactory; com.google.javascript.jscomp.RenamePrototypes |
| Closure | 158 | functional | 407 | 1: com.google.javascript.jscomp.CommandLineRunnerTest::testWarningGuardOrdering2; 2: com.google.javascript.jscomp.CommandLineRunnerTest::testWarningGuardOrdering4 | com.google.javascript.jscomp.AbstractCommandLineRunner; com.google.javascript.jscomp.CommandLineRunner; com.google.javascript.jscomp.DiagnosticGroups |
| Closure | 159 | functional | 423 | 1: com.google.javascript.jscomp.InlineFunctionsTest::testIssue423 | com.google.javascript.jscomp.InlineFunctions |
| Closure | 160 | functional | 467 | 1: com.google.javascript.jscomp.CommandLineRunnerTest::testCheckSymbolsOverrideForQuiet | com.google.javascript.jscomp.Compiler |
| Closure | 161 | functional | 522 | 1: com.google.javascript.jscomp.PeepholeFoldConstantsTest::testIssue522 | com.google.javascript.jscomp.PeepholeFoldConstants |
| Closure | 162 | functional | 548 | 1: com.google.javascript.jscomp.ScopedAliasesTest::testForwardJsDoc | com.google.javascript.jscomp.Scope; com.google.javascript.jscomp.ScopedAliases |
| Closure | 163 | functional | 600 | 1: com.google.javascript.jscomp.CrossModuleMethodMotionTest::testIssue600b; 2: com.google.javascript.jscomp.CrossModuleMethodMotionTest::testIssue600e; 3: com.google.javascript.jscomp.CrossModuleMethodMotionTest::testIssue600 | com.google.javascript.jscomp.AnalyzePrototypeProperties; com.google.javascript.jscomp.CrossModuleMethodMotion |
| Closure | 164 | functional | 634 | 1: com.google.javascript.jscomp.LooseTypeCheckTest::testMethodInference7; 2: com.google.javascript.jscomp.TypeCheckTest::testMethodInference7; 3: com.google.javascript.rhino.jstype.FunctionTypeTest::testSupAndInfOfReturnTypesWithNumOfParams | com.google.javascript.rhino.jstype.ArrowType |
| Closure | 165 | functional | 725 | 1: com.google.javascript.jscomp.TypeCheckTest::testIssue725 | 4 class(es) |
| Closure | 166 | exceptional | 785 | 1: com.google.javascript.jscomp.TypeInferenceTest::testRecordInference; 2: com.google.javascript.jscomp.TypeInferenceTest::testIssue785 | com.google.javascript.rhino.jstype.PrototypeObjectType |
| Closure | 167 | functional | 783 | 1: com.google.javascript.jscomp.TypeCheckTest::testIssue783; 2: com.google.javascript.jscomp.TypeCheckTest::testMissingProperty20; 3: com.google.javascript.rhino.jstype.JSTypeTest::testRestrictedTypeGivenToBoolean | com.google.javascript.jscomp.type.SemanticReverseAbstractInterpreter; com.google.javascript.rhino.jstype.JSType |
| Closure | 168 | functional | 726 | 1: com.google.javascript.jscomp.TypeCheckTest::testIssue726 | com.google.javascript.jscomp.TypedScopeCreator |
| Closure | 169 | functional | 791 | 1: com.google.javascript.jscomp.TypeCheckTest::testIssue791; 2: com.google.javascript.rhino.jstype.RecordTypeTest::testSubtypeWithUnknowns2 | 6 class(es) |
| Closure | 170 | functional | 965 | 1: com.google.javascript.jscomp.FlowSensitiveInlineVariablesTest::testVarAssinInsideHookIssue965 | com.google.javascript.jscomp.FlowSensitiveInlineVariables |
| Closure | 171 | functional | 1023 | 1: com.google.javascript.jscomp.TypeCheckTest::testIssue1023; 2: com.google.javascript.jscomp.TypedScopeCreatorTest::testMethodBeforeFunction2; 3: com.google.javascript.jscomp.TypedScopeCreatorTest::testPropertiesOnInterface2 | com.google.javascript.jscomp.TypeInference; com.google.javascript.jscomp.TypedScopeCreator |
| Closure | 172 | functional | 1042 | 1: com.google.javascript.jscomp.TypeCheckTest::testIssue1024 | com.google.javascript.jscomp.TypedScopeCreator |
| Closure | 173 | functional | 1062 | 1: com.google.javascript.jscomp.CodePrinterTest::testPrint; 2: com.google.javascript.jscomp.CodePrinterTest::testIssue1062; 3: com.google.javascript.jscomp.PeepholeSubstituteAlternateSyntaxTest::testAssocitivity | com.google.javascript.jscomp.CodeGenerator; com.google.javascript.jscomp.PeepholeSubstituteAlternateSyntax |
| Closure | 174 | functional | 1103 | 1: com.google.javascript.jscomp.ScopedAliasesTest::testIssue1103a; 2: com.google.javascript.jscomp.ScopedAliasesTest::testIssue1103b; 3: com.google.javascript.jscomp.ScopedAliasesTest::testIssue1103c | com.google.javascript.jscomp.JsAst; com.google.javascript.jscomp.NodeUtil; com.google.javascript.jscomp.ScopedAliases |
| Closure | 175 | functional | 1101 | 5 cause(s) | com.google.javascript.jscomp.FunctionInjector |
| Closure | 176 | functional | 1056 | 1: com.google.javascript.jscomp.TypeCheckTest::testIssue1056 | com.google.javascript.jscomp.TypeInference |
| Lang | 1 | exceptional | LANG-747 | 1: org.apache.commons.lang3.math.NumberUtilsTest::TestLang747 | org.apache.commons.lang3.math.NumberUtils |
| Lang | 3 | functional | LANG-693 | 1: org.apache.commons.lang3.math.NumberUtilsTest::testStringCreateNumberEnsureNoPrecisionLoss | org.apache.commons.lang3.math.NumberUtils |
| Lang | 4 | functional | LANG-882 | 1: org.apache.commons.lang3.text.translate.LookupTranslatorTest::testLang882 | org.apache.commons.lang3.text.translate.LookupTranslator |
| Lang | 5 | exceptional | LANG-865 | 1: org.apache.commons.lang3.LocaleUtilsTest::testLang865 | org.apache.commons.lang3.LocaleUtils |
| Lang | 6 | exceptional | LANG-857 | 1: org.apache.commons.lang3.StringUtilsTest::testEscapeSurrogatePairs | org.apache.commons.lang3.text.translate.CharSequenceTranslator |
| Lang | 7 | functional | LANG-822 | 1: org.apache.commons.lang3.math.NumberUtilsTest::testCreateNumber | org.apache.commons.lang3.math.NumberUtils |
| Lang | 8 | functional | LANG-818 | 1: org.apache.commons.lang3.time.FastDateFormat_PrinterTest::testCalendarTimezoneRespected; 2: org.apache.commons.lang3.time.FastDatePrinterTest::testCalendarTimezoneRespected | org.apache.commons.lang3.time.FastDatePrinter |
| Lang | 9 | functional | LANG-832 | 1: org.apache.commons.lang3.time.FastDateFormat_ParserTest::testLANG_832; 2: org.apache.commons.lang3.time.FastDateParserTest::testLANG_832 | org.apache.commons.lang3.time.FastDateParser |
| Lang | 10 | functional | LANG-831 | 1: org.apache.commons.lang3.time.FastDateFormat_ParserTest::testLANG_831; 2: org.apache.commons.lang3.time.FastDateParserTest::testLANG_831 | org.apache.commons.lang3.time.FastDateParser |
| Lang | 11 | functional | LANG-807 | 1: org.apache.commons.lang3.RandomStringUtilsTest::testLANG807 | org.apache.commons.lang3.RandomStringUtils |
| Lang | 12 | exceptional | LANG-805 | 1: org.apache.commons.lang3.RandomStringUtilsTest::testExceptions; 2: org.apache.commons.lang3.RandomStringUtilsTest::testLANG805 | org.apache.commons.lang3.RandomStringUtils |
| Lang | 13 | exceptional | LANG-788 | 1: org.apache.commons.lang3.SerializationUtilsTest::testPrimitiveTypeClassSerialization | org.apache.commons.lang3.SerializationUtils |
| Lang | 14 | functional | LANG-786 | 1: org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testEquals | org.apache.commons.lang3.StringUtils |
| Lang | 15 | functional | LANG-775 | 1: org.apache.commons.lang3.reflect.TypeUtilsTest::testGetTypeArguments; 2: org.apache.commons.lang3.reflect.TypeUtilsTest::testIsAssignable | org.apache.commons.lang3.reflect.TypeUtils |
| Lang | 16 | exceptional | LANG-746 | 1: org.apache.commons.lang3.math.NumberUtilsTest::testCreateNumber | org.apache.commons.lang3.math.NumberUtils |
| Lang | 17 | exceptional | LANG-720 | 1: org.apache.commons.lang3.StringEscapeUtilsTest::testLang720 | org.apache.commons.lang3.text.translate.CharSequenceTranslator |
| Lang | 19 | exceptional | LANG-710 | 1: org.apache.commons.lang3.text.translate.NumericEntityUnescaperTest::testUnfinishedEntity; 2: org.apache.commons.lang3.text.translate.NumericEntityUnescaperTest::testOutOfBounds | org.apache.commons.lang3.text.translate.NumericEntityUnescaper |
| Lang | 20 | exceptional | LANG-703 | 1: org.apache.commons.lang3.StringUtilsTest::testJoin_ArrayChar; 2: org.apache.commons.lang3.StringUtilsTest::testJoin_Objectarray | org.apache.commons.lang3.StringUtils |
| Lang | 21 | functional | LANG-677 | 1: org.apache.commons.lang3.time.DateUtilsTest::testIsSameLocalTime_Cal | org.apache.commons.lang3.time.DateUtils |
| Lang | 22 | functional | LANG-662 | 1: org.apache.commons.lang3.math.FractionTest::testReducedFactory_int_int; 2: org.apache.commons.lang3.math.FractionTest::testReduce | org.apache.commons.lang3.math.Fraction |
| Lang | 23 | functional | LANG-636 | 1: org.apache.commons.lang3.text.ExtendedMessageFormatTest::testEqualsHashcode | org.apache.commons.lang3.text.ExtendedMessageFormat |
| Lang | 24 | functional | LANG-664 | 1: org.apache.commons.lang3.math.NumberUtilsTest::testIsNumber | org.apache.commons.lang3.math.NumberUtils |
| Lang | 26 | exceptional | LANG-645 | 1: org.apache.commons.lang3.time.FastDateFormatTest::testLang645 | org.apache.commons.lang3.time.FastDateFormat |
| Lang | 27 | exceptional | LANG-638 | 1: org.apache.commons.lang3.math.NumberUtilsTest::testCreateNumber | org.apache.commons.lang3.math.NumberUtils |
| Lang | 28 | exceptional | LANG-617 | 1: org.apache.commons.lang3.text.translate.NumericEntityUnescaperTest::testSupplementaryUnescaping | org.apache.commons.lang3.text.translate.NumericEntityUnescaper |
| Lang | 29 | functional | LANG-624 | 1: org.apache.commons.lang3.SystemUtilsTest::testJavaVersionAsInt | org.apache.commons.lang3.SystemUtils |
| Lang | 30 | functional | LANG-607 | 10 cause(s) | org.apache.commons.lang3.StringUtils |
| Lang | 31 | functional | LANG-607 | 1: org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testContainsAnyCharArrayWithSupplementaryChars; 2: org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testContainsAnyStringWithSupplementaryChars | org.apache.commons.lang3.StringUtils |
| Lang | 32 | functional | LANG-586 | 1: org.apache.commons.lang3.builder.HashCodeBuilderTest::testReflectionObjectCycle | org.apache.commons.lang3.builder.HashCodeBuilder |
| Lang | 33 | exceptional | LANG-587 | 1: org.apache.commons.lang3.ClassUtilsTest::testToClass_object | org.apache.commons.lang3.ClassUtils |
| Lang | 34 | functional | LANG-586 | 27 cause(s) | org.apache.commons.lang3.builder.ToStringStyle |
| Lang | 35 | exceptional | LANG-571 | 1: org.apache.commons.lang3.ArrayUtilsAddTest::testLANG571 | org.apache.commons.lang3.ArrayUtils |
| Lang | 36 | functional | LANG-521 | 1: org.apache.commons.lang3.math.NumberUtilsTest::testCreateNumber; 2: org.apache.commons.lang3.math.NumberUtilsTest::testIsNumber | org.apache.commons.lang3.math.NumberUtils |
| Lang | 37 | exceptional | LANG-567 | 1: org.apache.commons.lang3.ArrayUtilsAddTest::testJira567 | org.apache.commons.lang3.ArrayUtils |
| Lang | 38 | exceptional | LANG-538 | 1: org.apache.commons.lang3.time.FastDateFormatTest::testLang538 | org.apache.commons.lang3.time.FastDateFormat |
| Lang | 39 | exceptional | LANG-552 | 1: org.apache.commons.lang3.StringUtilsTest::testReplace_StringStringArrayStringArray | org.apache.commons.lang3.StringUtils |
| Lang | 40 | functional | LANG-432 | 1: org.apache.commons.lang.StringUtilsEqualsIndexOfTest::testContainsIgnoreCase_LocaleIndependence | org.apache.commons.lang.StringUtils |
| Lang | 41 | exceptional | LANG-535 | 1: org.apache.commons.lang.ClassUtilsTest::test_getShortClassName_Class; 2: org.apache.commons.lang.ClassUtilsTest::test_getPackageName_Class | org.apache.commons.lang.ClassUtils |
| Lang | 42 | exceptional | LANG-480 | 1: org.apache.commons.lang.StringEscapeUtilsTest::testEscapeHtmlHighUnicode | org.apache.commons.lang.Entities |
| Lang | 43 | exceptional | LANG-477 | 1: org.apache.commons.lang.text.ExtendedMessageFormatTest::testEscapedQuote_LANG_477 | org.apache.commons.lang.text.ExtendedMessageFormat |
| Lang | 44 | exceptional | LANG-457 | 1: org.apache.commons.lang.NumberUtilsTest::testLang457 | org.apache.commons.lang.NumberUtils |
| Lang | 45 | exceptional | LANG-419 | 1: org.apache.commons.lang.WordUtilsTest::testAbbreviate | org.apache.commons.lang.WordUtils |
| Lang | 46 | exceptional | LANG-421 | 1: org.apache.commons.lang.StringEscapeUtilsTest::testEscapeJavaWithSlash | org.apache.commons.lang.StringEscapeUtils |
| Lang | 47 | exceptional | LANG-412 | 1: org.apache.commons.lang.text.StrBuilderTest::testLang412Left; 2: org.apache.commons.lang.text.StrBuilderTest::testLang412Right | org.apache.commons.lang.text.StrBuilder |
| Lang | 49 | functional | LANG-380 | 1: org.apache.commons.lang.math.FractionTest::testReduce | org.apache.commons.lang.math.Fraction |
| Lang | 50 | functional | LANG-368 | 1: org.apache.commons.lang.time.FastDateFormatTest::test_changeDefault_Locale_DateInstance; 2: org.apache.commons.lang.time.FastDateFormatTest::test_changeDefault_Locale_DateTimeInstance | org.apache.commons.lang.time.FastDateFormat |
| Lang | 51 | exceptional | LANG-365 | 1: org.apache.commons.lang.BooleanUtilsTest::test_toBoolean_String | org.apache.commons.lang.BooleanUtils |
| Lang | 52 | exceptional | LANG-363 | 1: org.apache.commons.lang.StringEscapeUtilsTest::testEscapeJavaScript | org.apache.commons.lang.StringEscapeUtils |
| Lang | 53 | functional | LANG-346 | 1: org.apache.commons.lang.time.DateUtilsTest::testRoundLang346 | org.apache.commons.lang.time.DateUtils |
| Lang | 54 | exceptional | LANG-328 | 1: org.apache.commons.lang.LocaleUtilsTest::testLang328 | org.apache.commons.lang.LocaleUtils |
| Lang | 55 | functional | LANG-315 | 1: org.apache.commons.lang.time.StopWatchTest::testLang315 | org.apache.commons.lang.time.StopWatch |
| Lang | 56 | exceptional | LANG-303 | 1: org.apache.commons.lang.time.FastDateFormatTest::testLang303 | org.apache.commons.lang.time.FastDateFormat |
| Lang | 57 | exceptional | LANG-304 | 11 cause(s) | org.apache.commons.lang.LocaleUtils |
| Lang | 58 | exceptional | LANG-300 | 1: org.apache.commons.lang.math.NumberUtilsTest::testLang300 | org.apache.commons.lang.math.NumberUtils |
| Lang | 59 | exceptional | LANG-299 | 1: org.apache.commons.lang.text.StrBuilderAppendInsertTest::testLang299 | org.apache.commons.lang.text.StrBuilder |
| Lang | 60 | functional | LANG-295 | 1: org.apache.commons.lang.text.StrBuilderTest::testLang295 | org.apache.commons.lang.text.StrBuilder |
| Lang | 61 | functional | LANG-294 | 1: org.apache.commons.lang.text.StrBuilderTest::testIndexOfLang294; 2: org.apache.commons.lang.text.StrBuilderTest::testLang294 | org.apache.commons.lang.text.StrBuilder |
| Lang | 62 | exceptional | LANG-292 | 1: org.apache.commons.lang.EntitiesTest::testNumberOverflow | org.apache.commons.lang.Entities |
| Lang | 63 | exceptional | LANG-281 | 1: org.apache.commons.lang.time.DurationFormatUtilsTest::testJiraLang281 | org.apache.commons.lang.time.DurationFormatUtils |
| Lang | 64 | functional | LANG-259 | 1: org.apache.commons.lang.enums.ValuedEnumTest::testCompareTo_otherEnumType | org.apache.commons.lang.enums.ValuedEnum |
| Lang | 65 | functional | LANG-59 | 1: org.apache.commons.lang.time.DateUtilsTest::testTruncateLang59 | org.apache.commons.lang.time.DateUtils |
| Math | 1 | exceptional | MATH-996 | 1: org.apache.commons.math3.fraction.BigFractionTest::testDigitLimitConstructor; 2: org.apache.commons.math3.fraction.FractionTest::testDigitLimitConstructor | org.apache.commons.math3.fraction.BigFraction; org.apache.commons.math3.fraction.Fraction |
| Math | 2 | functional | MATH-1021 | 1: org.apache.commons.math3.distribution.HypergeometricDistributionTest::testMath1021 | org.apache.commons.math3.distribution.HypergeometricDistribution |
| Math | 3 | exceptional | MATH-1005 | 1: org.apache.commons.math3.util.MathArraysTest::testLinearCombinationWithSingleElementArray | org.apache.commons.math3.util.MathArrays |
| Math | 4 | exceptional | MATH-988 | 1: org.apache.commons.math3.geometry.euclidean.threed.SubLineTest::testIntersectionNotIntersecting; 2: org.apache.commons.math3.geometry.euclidean.twod.SubLineTest::testIntersectionParallel | org.apache.commons.math3.geometry.euclidean.threed.SubLine; org.apache.commons.math3.geometry.euclidean.twod.SubLine |
| Math | 5 | functional | MATH-934 | 1: org.apache.commons.math3.complex.ComplexTest::testReciprocalZero | org.apache.commons.math3.complex.Complex |
| Math | 6 | functional | MATH-949 | 28 cause(s) | 7 class(es) |
| Math | 7 | functional | MATH-950 | 1: org.apache.commons.math3.ode.nonstiff.DormandPrince853IntegratorTest::testEventsScheduling | org.apache.commons.math3.ode.AbstractIntegrator |
| Math | 8 | exceptional | MATH-942 | 1: org.apache.commons.math3.distribution.DiscreteRealDistributionTest::testIssue942 | org.apache.commons.math3.distribution.DiscreteDistribution |
| Math | 9 | functional | MATH-938 | 1: org.apache.commons.math3.geometry.euclidean.threed.LineTest::testRevert | org.apache.commons.math3.geometry.euclidean.threed.Line |
| Math | 10 | functional | MATH-935 | 1: org.apache.commons.math3.analysis.differentiation.DerivativeStructureTest::testAtan2SpecialCases | org.apache.commons.math3.analysis.differentiation.DSCompiler |
| Math | 11 | functional | MATH-929 | 1: org.apache.commons.math3.distribution.MultivariateNormalDistributionTest::testUnivariateDistribution | org.apache.commons.math3.distribution.MultivariateNormalDistribution |
| Math | 12 | functional | MATH-927 | 1: org.apache.commons.math3.distribution.GammaDistributionTest::testDistributionClone; 2: org.apache.commons.math3.distribution.LogNormalDistributionTest::testDistributionClone; 3: org.apache.commons.math3.distribution.NormalDistributionTest::testDistributionClone | org.apache.commons.math3.random.BitsStreamGenerator |
| Math | 13 | exceptional | MATH-924 | 1: org.apache.commons.math3.optimization.fitting.PolynomialFitterTest::testLargeSample | org.apache.commons.math3.optimization.general.AbstractLeastSquaresOptimizer |
| Math | 14 | exceptional | MATH-924 | 1: org.apache.commons.math3.fitting.PolynomialFitterTest::testLargeSample | org.apache.commons.math3.optim.nonlinear.vector.jacobian.AbstractLeastSquaresOptimizer; org.apache.commons.math3.optim.nonlinear.vector.Weight |
| Math | 15 | functional | MATH-904 | 1: org.apache.commons.math3.util.FastMathTest::testMath904 | org.apache.commons.math3.util.FastMath |
| Math | 16 | functional | MATH-905 | 1: org.apache.commons.math3.util.FastMathTest::testMath905LargePositive; 2: org.apache.commons.math3.util.FastMathTest::testMath905LargeNegative | org.apache.commons.math3.util.FastMath |
| Math | 17 | functional | MATH-778 | 1: org.apache.commons.math3.dfp.DfpTest::testMultiply | org.apache.commons.math3.dfp.Dfp |
| Math | 18 | functional | MATH-867 | 1: org.apache.commons.math3.optimization.direct.CMAESOptimizerTest::testFitAccuracyDependsOnBoundary | org.apache.commons.math3.optimization.direct.CMAESOptimizer |
| Math | 19 | exceptional | MATH-865 | 1: org.apache.commons.math3.optimization.direct.CMAESOptimizerTest::testBoundaryRangeTooLarge | org.apache.commons.math3.optimization.direct.CMAESOptimizer |
| Math | 20 | functional | MATH-864 | 1: org.apache.commons.math3.optimization.direct.CMAESOptimizerTest::testMath864 | org.apache.commons.math3.optimization.direct.CMAESOptimizer |
| Math | 21 | functional | MATH-789 | 1: org.apache.commons.math3.linear.RectangularCholeskyDecompositionTest::testMath789; 2: org.apache.commons.math3.linear.RectangularCholeskyDecompositionTest::testFullRank | org.apache.commons.math3.linear.RectangularCholeskyDecomposition |
| Math | 22 | functional | MATH-859 | 1: org.apache.commons.math3.distribution.FDistributionTest::testIsSupportLowerBoundInclusive; 2: org.apache.commons.math3.distribution.UniformRealDistributionTest::testIsSupportUpperBoundInclusive | org.apache.commons.math3.distribution.FDistribution; org.apache.commons.math3.distribution.UniformRealDistribution |
| Math | 23 | functional | MATH-855 | 1: org.apache.commons.math3.optimization.univariate.BrentOptimizerTest::testKeepInitIfBest | org.apache.commons.math3.optimization.univariate.BrentOptimizer |
| Math | 24 | functional | MATH-855 | 1: org.apache.commons.math3.optimization.univariate.BrentOptimizerTest::testMath855 | org.apache.commons.math3.optimization.univariate.BrentOptimizer |
| Math | 25 | functional | MATH-844 | 1: org.apache.commons.math3.optimization.fitting.HarmonicFitterTest::testMath844 | org.apache.commons.math3.optimization.fitting.HarmonicFitter |
| Math | 26 | functional | MATH-836 | 1: org.apache.commons.math3.fraction.FractionTest::testIntegerOverflow | org.apache.commons.math3.fraction.Fraction |
| Math | 27 | functional | MATH-835 | 1: org.apache.commons.math3.fraction.FractionTest::testMath835 | org.apache.commons.math3.fraction.Fraction |
| Math | 28 | exceptional | MATH-828 | 1: org.apache.commons.math3.optimization.linear.SimplexSolverTest::testMath828Cycle | org.apache.commons.math3.optimization.linear.SimplexSolver |
| Math | 29 | functional | MATH-803 | 1: org.apache.commons.math3.linear.SparseRealVectorTest::testEbeDivideMixedTypes; 2: org.apache.commons.math3.linear.SparseRealVectorTest::testEbeMultiplyMixedTypes; 3: org.apache.commons.math3.linear.SparseRealVectorTest::testEbeMultiplySameType | org.apache.commons.math3.linear.OpenMapRealVector |
| Math | 30 | functional | MATH-790 | 1: org.apache.commons.math3.stat.inference.MannWhitneyUTestTest::testBigDataSet | org.apache.commons.math3.stat.inference.MannWhitneyUTest |
| Math | 31 | functional | MATH-718 | 1: org.apache.commons.math3.distribution.BinomialDistributionTest::testMath718; 2: org.apache.commons.math3.distribution.FDistributionTest::testMath785 | org.apache.commons.math3.util.ContinuedFraction |
| Math | 32 | exceptional | MATH-780 | 1: org.apache.commons.math3.geometry.euclidean.threed.PolyhedronsSetTest::testIssue780 | org.apache.commons.math3.geometry.euclidean.twod.PolygonsSet |
| Math | 33 | functional | MATH-781 | 1: org.apache.commons.math3.optimization.linear.SimplexSolverTest::testMath781 | org.apache.commons.math3.optimization.linear.SimplexTableau |
| Math | 34 | functional | MATH-779 | 1: org.apache.commons.math3.genetics.ListPopulationTest::testIterator | org.apache.commons.math3.genetics.ListPopulation |
| Math | 35 | functional | MATH-776 | 4 cause(s) | org.apache.commons.math3.genetics.ElitisticListPopulation |
| Math | 36 | functional | MATH-744 | 1: org.apache.commons.math.fraction.BigFractionTest::testFloatValueForLargeNumeratorAndDenominator; 2: org.apache.commons.math.fraction.BigFractionTest::testDoubleValueForLargeNumeratorAndDenominator | org.apache.commons.math.fraction.BigFraction |
| Math | 37 | functional | MATH-722 | 4 cause(s) | org.apache.commons.math.complex.Complex |
| Math | 38 | exceptional | MATH-728 | 1: org.apache.commons.math.optimization.direct.BOBYQAOptimizerTest::testConstrainedRosenWithMoreInterpolationPoints | org.apache.commons.math.optimization.direct.BOBYQAOptimizer |
| Math | 39 | functional | MATH-727 | 1: org.apache.commons.math.ode.nonstiff.DormandPrince853IntegratorTest::testTooLargeFirstStep | org.apache.commons.math.ode.nonstiff.EmbeddedRungeKuttaIntegrator |
| Math | 40 | exceptional | MATH-716 | 1: org.apache.commons.math.analysis.solvers.BracketingNthOrderBrentSolverTest::testIssue716 | org.apache.commons.math.analysis.solvers.BracketingNthOrderBrentSolver |
| Math | 41 | functional | MATH-704 | 1: org.apache.commons.math.stat.descriptive.moment.VarianceTest::testEvaluateArraySegmentWeighted | org.apache.commons.math.stat.descriptive.moment.Variance |
| Math | 42 | functional | MATH-713 | 1: org.apache.commons.math.optimization.linear.SimplexSolverTest::testMath713NegativeVariable | org.apache.commons.math.optimization.linear.SimplexTableau |
| Math | 43 | functional | MATH-691 | 6 cause(s) | org.apache.commons.math.stat.descriptive.SummaryStatistics |
| Math | 44 | functional | MATH-695 | 1: org.apache.commons.math.ode.events.EventStateTest::testIssue695 | org.apache.commons.math.ode.AbstractIntegrator |
| Math | 45 | functional | MATH-679 | 1: org.apache.commons.math.linear.OpenMapRealMatrixTest::testMath679 | org.apache.commons.math.linear.OpenMapRealMatrix |
| Math | 46 | functional | MATH-657 | 1: org.apache.commons.math.complex.ComplexTest::testAtanI; 2: org.apache.commons.math.complex.ComplexTest::testDivideZero | org.apache.commons.math.complex.Complex |
| Math | 47 | functional | MATH-657 | 1: org.apache.commons.math.complex.ComplexTest::testAtanI; 2: org.apache.commons.math.complex.ComplexTest::testDivideZero | org.apache.commons.math.complex.Complex |
| Math | 48 | exceptional | MATH-631 | 1: org.apache.commons.math.analysis.solvers.RegulaFalsiSolverTest::testIssue631 | org.apache.commons.math.analysis.solvers.BaseSecantSolver |
| Math | 49 | exceptional | MATH-645 | 1: org.apache.commons.math.linear.SparseRealVectorTest::testConcurrentModification | org.apache.commons.math.linear.OpenMapRealVector |
| Math | 50 | functional | MATH-631 | 1: org.apache.commons.math.analysis.solvers.RegulaFalsiSolverTest::testIssue631 | org.apache.commons.math.analysis.solvers.BaseSecantSolver |
| Math | 51 | exceptional | MATH-631 | 1: org.apache.commons.math.analysis.solvers.RegulaFalsiSolverTest::testIssue631 | org.apache.commons.math.analysis.solvers.BaseSecantSolver |
| Math | 52 | functional | MATH-639 | 1: org.apache.commons.math.geometry.euclidean.threed.RotationTest::testIssue639 | org.apache.commons.math.geometry.euclidean.threed.Rotation |
| Math | 53 | functional | MATH-618 | 1: org.apache.commons.math.complex.ComplexTest::testAddNaN | org.apache.commons.math.complex.Complex |
| Math | 54 | functional | MATH-567 | 1: org.apache.commons.math.dfp.DfpTest::testIssue567 | org.apache.commons.math.dfp.Dfp |
| Math | 55 | functional | MATH-554 | 1: org.apache.commons.math.geometry.Vector3DTest::testCrossProductCancellation | org.apache.commons.math.geometry.Vector3D |
| Math | 56 | functional | MATH-552 | 1: org.apache.commons.math.util.MultidimensionalCounterTest::testIterationConsistency | org.apache.commons.math.util.MultidimensionalCounter |
| Math | 57 | functional | MATH-546 | 1: org.apache.commons.math.stat.clustering.KMeansPlusPlusClustererTest::testSmallDistances | org.apache.commons.math.stat.clustering.KMeansPlusPlusClusterer |
| Math | 58 | exceptional | MATH-519 | 1: org.apache.commons.math.optimization.fitting.GaussianFitterTest::testMath519 | org.apache.commons.math.optimization.fitting.GaussianFitter |
| Math | 59 | functional | MATH-482 | 1: org.apache.commons.math.util.FastMathTest::testMinMaxFloat | org.apache.commons.math.util.FastMath |
| Math | 60 | exceptional | MATH-414 | 1: org.apache.commons.math.distribution.NormalDistributionTest::testExtremeValues | org.apache.commons.math.distribution.NormalDistributionImpl |
| Math | 61 | exceptional | MATH-349 | 1: org.apache.commons.math.distribution.PoissonDistributionTest::testMean | org.apache.commons.math.distribution.PoissonDistributionImpl |
| Math | 62 | functional | MATH-413 | 1: org.apache.commons.math.optimization.univariate.MultiStartUnivariateRealOptimizerTest::testQuinticMin | org.apache.commons.math.optimization.univariate.MultiStartUnivariateRealOptimizer |
| Math | 63 | functional | MATH-370 | 1: org.apache.commons.math.util.MathUtilsTest::testArrayEquals | org.apache.commons.math.util.MathUtils |
| Math | 64 | functional | MATH-405 | 1: org.apache.commons.math.optimization.general.MinpackTest::testMinpackJennrichSampson; 2: org.apache.commons.math.optimization.general.MinpackTest::testMinpackFreudensteinRoth | org.apache.commons.math.optimization.general.LevenbergMarquardtOptimizer |
| Math | 65 | functional | MATH-377 | 1: org.apache.commons.math.optimization.general.LevenbergMarquardtOptimizerTest::testCircleFitting | org.apache.commons.math.optimization.general.AbstractLeastSquaresOptimizer |
| Math | 66 | functional | MATH-395 | 4 cause(s) | org.apache.commons.math.optimization.univariate.BrentOptimizer |
| Math | 67 | functional | MATH-393 | 1: org.apache.commons.math.optimization.MultiStartUnivariateRealOptimizerTest::testQuinticMin | org.apache.commons.math.optimization.MultiStartUnivariateRealOptimizer |
| Math | 68 | functional | MATH-362 | 1: org.apache.commons.math.optimization.general.MinpackTest::testMinpackJennrichSampson; 2: org.apache.commons.math.optimization.general.MinpackTest::testMinpackFreudensteinRoth | org.apache.commons.math.optimization.general.LevenbergMarquardtOptimizer |
| Math | 69 | functional | MATH-371 | 1: org.apache.commons.math.stat.correlation.PearsonsCorrelationTest::testPValueNearZero; 2: org.apache.commons.math.stat.correlation.SpearmansRankCorrelationTest::testPValueNearZero | org.apache.commons.math.stat.correlation.PearsonsCorrelation |
| Math | 70 | exceptional | MATH-369 | 1: org.apache.commons.math.analysis.solvers.BisectionSolverTest::testMath369 | org.apache.commons.math.analysis.solvers.BisectionSolver |
| Math | 71 | functional | MATH-358 | 1: org.apache.commons.math.ode.nonstiff.ClassicalRungeKuttaIntegratorTest::testMissedEndEvent; 2: org.apache.commons.math.ode.nonstiff.DormandPrince853IntegratorTest::testMissedEndEvent | org.apache.commons.math.ode.nonstiff.EmbeddedRungeKuttaIntegrator; org.apache.commons.math.ode.nonstiff.RungeKuttaIntegrator |
| Math | 72 | functional | MATH-344 | 1: org.apache.commons.math.analysis.solvers.BrentSolverTest::testRootEndpoints | org.apache.commons.math.analysis.solvers.BrentSolver |
| Math | 73 | functional | MATH-343 | 1: org.apache.commons.math.analysis.solvers.BrentSolverTest::testBadEndpoints | org.apache.commons.math.analysis.solvers.BrentSolver |
| Math | 74 | functional | MATH-338 | 1: org.apache.commons.math.ode.nonstiff.AdamsMoultonIntegratorTest::polynomial | org.apache.commons.math.ode.nonstiff.EmbeddedRungeKuttaIntegrator |
| Math | 75 | functional | MATH-329 | 1: org.apache.commons.math.stat.FrequencyTest::testPcts | org.apache.commons.math.stat.Frequency |
| Math | 76 | functional | MATH-320 | 1: org.apache.commons.math.linear.SingularValueSolverTest::testMath320A; 2: org.apache.commons.math.linear.SingularValueSolverTest::testMath320B | org.apache.commons.math.linear.SingularValueDecompositionImpl |
| Math | 77 | functional | MATH-326 | 1: org.apache.commons.math.linear.ArrayRealVectorTest::testBasicFunctions; 2: org.apache.commons.math.linear.SparseRealVectorTest::testBasicFunctions | org.apache.commons.math.linear.ArrayRealVector; org.apache.commons.math.linear.OpenMapRealVector |
| Math | 78 | exceptional | MATH-322 | 1: org.apache.commons.math.ode.events.EventStateTest::closeEvents | org.apache.commons.math.ode.events.EventState |
| Math | 79 | exceptional | MATH-305 | 1: org.apache.commons.math.stat.clustering.KMeansPlusPlusClustererTest::testPerformClusterAnalysisDegenerate | org.apache.commons.math.util.MathUtils |
| Math | 80 | functional | MATH-318 | 1: org.apache.commons.math.linear.EigenDecompositionImplTest::testMathpbx02 | org.apache.commons.math.linear.EigenDecompositionImpl |
| Math | 81 | exceptional | MATH-308 | 1: org.apache.commons.math.linear.EigenDecompositionImplTest::testMath308 | org.apache.commons.math.linear.EigenDecompositionImpl |
| Math | 82 | functional | MATH-288 | 1: org.apache.commons.math.optimization.linear.SimplexSolverTest::testMath288 | org.apache.commons.math.optimization.linear.SimplexSolver |
| Math | 83 | functional | MATH-286 | 1: org.apache.commons.math.optimization.linear.SimplexSolverTest::testMath286 | org.apache.commons.math.optimization.linear.SimplexTableau |
| Math | 84 | functional | MATH-283 | 1: org.apache.commons.math.optimization.direct.MultiDirectionalTest::testMinimizeMaximize; 2: org.apache.commons.math.optimization.direct.MultiDirectionalTest::testMath283 | org.apache.commons.math.optimization.direct.MultiDirectional |
| Math | 85 | exceptional | MATH-280 | 1: org.apache.commons.math.distribution.NormalDistributionTest::testMath280 | org.apache.commons.math.analysis.solvers.UnivariateRealSolverUtils |
| Math | 86 | functional | MATH-274 | 1: org.apache.commons.math.linear.CholeskyDecompositionImplTest::testMath274; 2: org.apache.commons.math.linear.CholeskyDecompositionImplTest::testNotPositiveDefinite | org.apache.commons.math.linear.CholeskyDecompositionImpl |
| Math | 87 | functional | MATH-273 | 1: org.apache.commons.math.optimization.linear.SimplexSolverTest::testSingleVariableAndConstraint | org.apache.commons.math.optimization.linear.SimplexTableau |
| Math | 88 | functional | MATH-272 | 1: org.apache.commons.math.optimization.linear.SimplexSolverTest::testMath272 | org.apache.commons.math.optimization.linear.SimplexTableau |
| Math | 89 | exceptional | MATH-259 | 1: org.apache.commons.math.stat.FrequencyTest::testAddNonComparable | org.apache.commons.math.stat.Frequency |
| Math | 90 | exceptional | MATH-259 | 1: org.apache.commons.math.stat.FrequencyTest::testAddNonComparable | org.apache.commons.math.stat.Frequency |
| Math | 91 | functional | MATH-252 | 1: org.apache.commons.math.fraction.FractionTest::testCompareTo | org.apache.commons.math.fraction.Fraction |
| Math | 92 | functional | MATH-241 | 1: org.apache.commons.math.util.MathUtilsTest::testBinomialCoefficientLarge | org.apache.commons.math.util.MathUtils |
| Math | 93 | functional | MATH-240 | 1: org.apache.commons.math.util.MathUtilsTest::testFactorial | org.apache.commons.math.util.MathUtils |
| Math | 94 | functional | MATH-238 | 1: org.apache.commons.math.util.MathUtilsTest::testGcd | org.apache.commons.math.util.MathUtils |
| Math | 95 | exceptional | MATH-227 | 1: org.apache.commons.math.distribution.FDistributionTest::testSmallDegreesOfFreedom | org.apache.commons.math.distribution.FDistributionImpl |
| Math | 96 | functional | MATH-221 | 1: org.apache.commons.math.complex.ComplexTest::testMath221 | org.apache.commons.math.complex.Complex |
| Math | 97 | exceptional | MATH-204 | 1: org.apache.commons.math.analysis.BrentSolverTest::testRootEndpoints | org.apache.commons.math.analysis.BrentSolver |
| Math | 98 | exceptional | MATH-209 | 1: org.apache.commons.math.linear.BigMatrixImplTest::testMath209; 2: org.apache.commons.math.linear.RealMatrixImplTest::testMath209 | org.apache.commons.math.linear.BigMatrixImpl; org.apache.commons.math.linear.RealMatrixImpl |
| Math | 99 | functional | MATH-243 | 1: org.apache.commons.math.util.MathUtilsTest::testGcd; 2: org.apache.commons.math.util.MathUtilsTest::testLcm | org.apache.commons.math.util.MathUtils |
| Math | 100 | exceptional | MATH-200 | 1: org.apache.commons.math.estimation.GaussNewtonEstimatorTest::testBoundParameters | org.apache.commons.math.estimation.AbstractEstimator |
| Math | 101 | exceptional | MATH-198 | 1: org.apache.commons.math.complex.ComplexFormatTest::testForgottenImaginaryCharacter; 2: org.apache.commons.math.complex.FrenchComplexFormatTest::testForgottenImaginaryCharacter | org.apache.commons.math.complex.ComplexFormat |
| Math | 102 | functional | MATH-175 | 6 cause(s) | org.apache.commons.math.stat.inference.ChiSquareTestImpl |
| Math | 103 | exceptional | MATH-167 | 1: org.apache.commons.math.distribution.NormalDistributionTest::testExtremeValues | org.apache.commons.math.distribution.NormalDistributionImpl |
| Math | 104 | functional | MATH-166 | 1: org.apache.commons.math.special.GammaTest::testRegularizedGammaPositivePositive | org.apache.commons.math.special.Gamma |
| Math | 105 | functional | MATH-85 | 1: org.apache.commons.math.stat.regression.SimpleRegressionTest::testSSENonNegative | org.apache.commons.math.stat.regression.SimpleRegression |
| Math | 106 | functional | MATH-60 | 1: org.apache.commons.math.fraction.FractionFormatTest::testParseProperInvalidMinus | org.apache.commons.math.fraction.ProperFractionFormat |
| Mockito | 1 | exceptional | 188 | 26 cause(s) | org.mockito.internal.invocation.InvocationMatcher |
| Mockito | 2 | functional | 197 | 1: org.mockito.internal.util.TimerTest::should_throw_friendly_reminder_exception_when_duration_is_negative; 2: org.mockito.verification.NegativeDurationTest::should_throw_exception_when_duration_is_negative_for_timeout_method; 3: org.mockito.verification.NegativeDurationTest::should_throw_exception_when_duration_is_negative_for_after_method | org.mockito.internal.util.Timer |
| Mockito | 3 | functional | 188 | 9 cause(s) | org.mockito.internal.invocation.InvocationMatcher |
| Mockito | 4 | exceptional | 187 | 4 cause(s) | org.mockito.exceptions.Reporter |
| Mockito | 5 | functional | 152 | 1: org.mockitointegration.NoJUnitDependenciesTest::pure_mockito_should_not_depend_JUnit | org.mockito.internal.verification.VerificationOverTimeImpl |
| Mockito | 6 | exceptional | 134 | 7 cause(s) | org.mockito.Matchers |
| Mockito | 7 | exceptional | 128 | 1: org.mockitousage.bugs.deepstubs.DeepStubFailingWhenGenricNestedAsRawTypeTest::discoverDeepMockingOfGenerics | org.mockito.internal.util.reflection.GenericMetadataSupport |
| Mockito | 8 | exceptional | 114 | 1: org.mockito.internal.util.reflection.GenericMetadataSupportTest::typeVariable_of_self_type | org.mockito.internal.util.reflection.GenericMetadataSupport |
| Mockito | 9 | exceptional | 122 | 1: org.mockitousage.constructor.CreatingMocksWithConstructorTest::abstractMethodStubbed; 2: org.mockitousage.constructor.CreatingMocksWithConstructorTest::testCallsRealInterfaceMethod; 3: org.mockitousage.constructor.CreatingMocksWithConstructorTest::abstractMethodReturnsDefault | org.mockito.internal.stubbing.answers.CallsRealMethods |
| Mockito | 10 | exceptional | 99 | 1: org.mockitousage.bugs.DeepStubsWronglyReportsSerializationProblemsTest::should_not_raise_a_mockito_exception_about_serialization_when_accessing_deep_stub | org.mockito.internal.stubbing.defaultanswers.ReturnsDeepStubs |
| Mockito | 11 | functional | 87 | 1: org.mockito.internal.creation.DelegatingMethodTest::equals_should_return_true_when_equal; 2: org.mockito.internal.creation.DelegatingMethodTest::equals_should_return_true_when_self | org.mockito.internal.creation.DelegatingMethod |
| Mockito | 12 | exceptional | 188 | 10 cause(s) | org.mockito.internal.util.reflection.GenericMaster |
| Mockito | 13 | functional | 138 | 1: org.mockitousage.bugs.VerifyingWithAnExtraCallToADifferentMockTest::shouldAllowVerifyingWhenOtherMockCallIsInTheSameLine | org.mockito.internal.MockHandler |
| Mockito | 14 | functional | 138 | 1: org.mockitousage.bugs.VerifyingWithAnExtraCallToADifferentMockTest::shouldAllowVerifyingWhenOtherMockCallIsInTheSameLine | org.mockito.internal.MockHandler; org.mockito.internal.MockitoCore |
| Mockito | 15 | functional | 211 | 1: org.mockitousage.bugs.InjectMocksShouldTryPropertySettersFirstBeforeFieldAccessTest::shouldInjectUsingPropertySetterIfAvailable | org.mockito.internal.configuration.injection.FinalMockCandidateFilter |
| Mockito | 16 | exceptional | 151 | 1: org.mockitousage.bugs.StubbingMocksThatAreConfiguredToReturnMocksTest::shouldAllowStubbingMocksConfiguredWithRETURNS_MOCKS | org.mockito.internal.MockitoCore; org.mockito.Mockito |
| Mockito | 17 | exceptional | 152 | 1: org.mockitousage.basicapi.MocksSerializationTest::shouldBeSerializeAndHaveExtraInterfaces | org.mockito.internal.creation.MockSettingsImpl; org.mockito.internal.util.MockUtil |
| Mockito | 18 | exceptional | 210 | 1: org.mockito.internal.stubbing.defaultanswers.ReturnsEmptyValuesTest::should_return_empty_iterable | org.mockito.internal.stubbing.defaultanswers.ReturnsEmptyValues |
| Mockito | 19 | functional | 205 | 1: org.mockitousage.annotation.MockInjectionUsingSetterOrPropertyTest::shouldInsertFieldWithCorrectNameWhenMultipleTypesAvailable | 5 class(es) |
| Mockito | 20 | functional | 92 | 8 cause(s) | org.mockito.internal.creation.bytebuddy.ByteBuddyMockMaker |
| Mockito | 21 | exceptional | 92 | 1: org.mockito.internal.creation.instance.ConstructorInstantiatorTest::creates_instances_of_inner_classes | org.mockito.internal.creation.instance.ConstructorInstantiator |
| Mockito | 22 | exceptional | 484 | 1: org.mockito.internal.matchers.EqualityTest::shouldKnowIfObjectsAreEqual | org.mockito.internal.matchers.Equality |
| Mockito | 23 | exceptional | 399 | 1: org.mockitousage.stubbing.DeepStubsSerializableTest::should_serialize_and_deserialize_mock_created_by_deep_stubs | org.mockito.internal.stubbing.defaultanswers.ReturnsDeepStubs |
| Mockito | 24 | functional | 467 | 1: org.mockito.internal.stubbing.defaultanswers.ReturnsEmptyValuesTest::should_return_zero_if_mock_is_compared_to_itself; 2: org.mockitousage.bugs.ShouldMocksCompareToBeConsistentWithEqualsTest::should_compare_to_be_consistent_with_equals_when_comparing_the_same_reference | org.mockito.internal.stubbing.defaultanswers.ReturnsEmptyValues |
| Mockito | 25 | exceptional | 230 | 6 cause(s) | org.mockito.internal.stubbing.defaultanswers.ReturnsDeepStubs |
| Mockito | 26 | functional | 352 | 4 cause(s) | org.mockito.internal.util.Primitives |
| Mockito | 27 | functional | 282 | 1: org.mockitousage.bugs.ListenersLostOnResetMockTest::listener | org.mockito.internal.util.MockUtil |
| Mockito | 28 | functional | 236 | 1: org.mockitousage.bugs.InjectionByTypeShouldFirstLookForExactTypeThenAncestorTest::mock_should_be_injected_once_and_in_the_best_matching_type | org.mockito.internal.configuration.DefaultInjectionEngine |
| Mockito | 29 | exceptional | 229 | 1: org.mockitousage.bugs.NPEWithCertainMatchersTest::shouldNotThrowNPEWhenNullPassedToSame | org.mockito.internal.matchers.Same |
| Mockito | 30 | functional | 225 | 1: org.mockito.internal.stubbing.defaultanswers.ReturnsSmartNullsTest::shouldPrintTheParametersOnSmartNullPointerExceptionMessage | org.mockito.exceptions.Reporter; org.mockito.internal.stubbing.defaultanswers.ReturnsSmartNulls |
| Mockito | 31 | exceptional | 225 | 1: org.mockito.internal.stubbing.defaultanswers.ReturnsSmartNullsTest::shouldPrintTheParametersWhenCallingAMethodWithArgs | org.mockito.internal.stubbing.defaultanswers.ReturnsSmartNulls |
| Mockito | 32 | functional | 216 | 1: org.mockitousage.bugs.SpyShouldHaveNiceNameTest::shouldPrintNiceName | org.mockito.internal.configuration.SpyAnnotationEngine |
| Mockito | 33 | functional | 200 | 1: org.mockitousage.bugs.InheritedGenericsPolimorphicCallTest::shouldStubbingWork; 2: org.mockitousage.bugs.InheritedGenericsPolimorphicCallTest::shouldVerificationWorks | org.mockito.internal.invocation.InvocationMatcher |
| Mockito | 34 | exceptional | 157 | 1: org.mockito.internal.invocation.InvocationMatcherTest::shouldMatchCaptureArgumentsWhenArgsCountDoesNOTMatch; 2: org.mockitousage.basicapi.UsingVarargsTest::shouldMatchEasilyEmptyVararg | org.mockito.internal.invocation.InvocationMatcher |
| Mockito | 35 | exceptional | 98 | 4 cause(s) | org.mockito.Matchers |
| Mockito | 36 | exceptional | 140 | 1: org.mockito.internal.invocation.InvocationTest::shouldScreamWhenCallingRealMethodOnInterface; 2: org.mockitousage.spies.SpyingOnInterfacesTest::shouldFailInRuntimeWhenCallingRealMethodOnInterface | org.mockito.internal.invocation.Invocation |
| Mockito | 37 | functional | 140 | 1: org.mockito.internal.stubbing.answers.AnswersValidatorTest::shouldFailWhenCallingRealMethodOnIterface; 2: org.mockitousage.spies.SpyingOnInterfacesTest::shouldFailFastWhenCallingRealMethodOnInterface | org.mockito.internal.stubbing.answers.AnswersValidator |
| Mockito | 38 | exceptional | 79 | 1: org.mockito.internal.verification.argumentmatching.ArgumentMatchingToolTest::shouldWorkFineWhenGivenArgIsNull; 2: org.mockitousage.bugs.ActualInvocationHasNullArgumentNPEBugTest::shouldAllowPassingNullArgument | org.mockito.internal.verification.argumentmatching.ArgumentMatchingTool |
| Time | 1 | functional | 93 | 1: org.joda.time.TestPartial_Constructors::testConstructorEx7_TypeArray_intArray | org.joda.time.field.UnsupportedDurationField; org.joda.time.Partial |
| Time | 2 | exceptional | 93 | 1: org.joda.time.TestPartial_Basics::testWith_baseAndArgHaveNoRange | org.joda.time.field.UnsupportedDurationField; org.joda.time.Partial |
| Time | 3 | exceptional | 77 | 5 cause(s) | org.joda.time.MutableDateTime |
| Time | 4 | functional | 88 | 1: org.joda.time.TestPartial_Basics::testWith3 | org.joda.time.Partial |
| Time | 5 | exceptional | 79 | 1: org.joda.time.TestPeriod_Basics::testNormalizedStandard_periodType_months1; 2: org.joda.time.TestPeriod_Basics::testNormalizedStandard_periodType_months2; 3: org.joda.time.TestPeriod_Basics::testNormalizedStandard_periodType_monthsWeeks | org.joda.time.Period |
| Time | 6 | functional | 28 | 5 cause(s) | org.joda.time.chrono.GJChronology |
| Time | 7 | exceptional | 21 | 1: org.joda.time.format.TestDateTimeFormatter::testParseInto_monthDay_feb29_newYork_startOfYear; 2: org.joda.time.format.TestDateTimeFormatter::testParseInto_monthDay_feb29_tokyo_endOfYear | org.joda.time.format.DateTimeFormatter |
| Time | 8 | exceptional | 42 | 1: org.joda.time.TestDateTimeZone::testForOffsetHoursMinutes_int_int | org.joda.time.DateTimeZone |
| Time | 9 | functional | 43 | 1: org.joda.time.TestDateTimeZone::testForOffsetHoursMinutes_int_int | org.joda.time.DateTimeZone |
| Time | 10 | exceptional | 22 | 1: org.joda.time.TestDays::testFactory_daysBetween_RPartial_MonthDay; 2: org.joda.time.TestMonths::testFactory_monthsBetween_RPartial_MonthDay | org.joda.time.base.BaseSingleFieldPeriod |
| Time | 11 | functional | 18 | 1: org.joda.time.tz.TestCompiler::testDateTimeZoneBuilder | org.joda.time.tz.ZoneInfoCompiler |
| Time | 12 | functional | 8 | 8 cause(s) | org.joda.time.LocalDate; org.joda.time.LocalDateTime |
| Time | 13 | exceptional | 160 | 1: org.joda.time.format.TestISOPeriodFormat::testFormatStandard_negative | org.joda.time.format.PeriodFormatterBuilder |
| Time | 14 | functional | 151 | 8 cause(s) | org.joda.time.chrono.BasicMonthOfYearDateTimeField |
| Time | 15 | functional | 147 | 1: org.joda.time.field.TestFieldUtils::testSafeMultiplyLongInt | org.joda.time.field.FieldUtils |
| Time | 16 | functional | 148 | 7 cause(s) | org.joda.time.format.DateTimeFormatter |
| Time | 17 | functional | 141 | 1: org.joda.time.TestDateTimeZoneCutover::testBug3476684_adjustOffset | org.joda.time.DateTimeZone |
| Time | 18 | exceptional | 130 | 1: org.joda.time.chrono.TestGJChronology::testLeapYearRulesConstruction | org.joda.time.chrono.GJChronology |
| Time | 19 | exceptional | 124 | 1: org.joda.time.TestDateTimeZoneCutover::testDateTimeCreation_london | org.joda.time.DateTimeZone |
| Time | 20 | exceptional | 126 | 1: org.joda.time.format.TestDateTimeFormatterBuilder::test_printParseZoneDawsonCreek | org.joda.time.format.DateTimeFormatterBuilder |
| Time | 22 | functional | 113 | 1: org.joda.time.TestDuration_Basics::testToPeriod_fixedZone; 2: org.joda.time.TestPeriod_Constructors::testConstructor_long_fixedZone | org.joda.time.base.BasePeriod |
| Time | 23 | exceptional | 112 | 1: org.joda.time.TestDateTimeZone::testForID_String_old | org.joda.time.DateTimeZone |
| Time | 24 | functional | 107 | 7 cause(s) | org.joda.time.format.DateTimeParserBucket |
| Time | 25 | exceptional | 90 | 1: org.joda.time.TestDateTimeZoneCutover::test_DateTime_constructor_Moscow_Autumn; 2: org.joda.time.TestDateTimeZoneCutover::test_getOffsetFromLocal_Moscow_Autumn_overlap_mins; 3: org.joda.time.TestDateTimeZoneCutover::test_getOffsetFromLocal_Moscow_Autumn | org.joda.time.DateTimeZone |
| Time | 26 | functional | 60 | 8 cause(s) | org.joda.time.chrono.ZonedChronology; org.joda.time.DateTimeZone; org.joda.time.field.LenientDateTimeField |
| Time | 27 | exceptional | 64 | 1: org.joda.time.format.TestPeriodFormatterBuilder::testBug2495455 | org.joda.time.format.PeriodFormatterBuilder |

